import datetime
import uuid
from copy import deepcopy

import sqlalchemy as sa
import marshmallow as ma
from cel_expr_python.cel import NewEnv, Type
from marshmallow import pre_load, post_load, validates_schema, ValidationError

from gn_module_monitoring.config.utils import apply_substitutions
from gn_module_monitoring.tools.utils import CELValidationsField, check_cel_type
from .fields import EntityFieldConfigSchema, schema_context

# Types CEL des valeurs Python des stores (par type Python de la valeur chargée) :
CEL_TYPES_MAP = {
    int: Type("google.protobuf.Int64Value"),
    float: Type("google.protobuf.DoubleValue"),
    bool: Type("google.protobuf.BoolValue"),
    str: Type("google.protobuf.StringValue"),
    uuid.UUID: Type("google.protobuf.StringValue"),  # converti en chaîne pour CEL
    datetime.date: Type("google.protobuf.Timestamp"),
    datetime.datetime: Type("google.protobuf.Timestamp"),
}


def check_cel_types(fields_def, entity_validate_cel):
    """
    Vérifie le typage des expressions CEL d’une entité, les variables `fields.<nom>` étant
    typées par le store de chaque champ.
    """
    env = NewEnv(
        variables={
            f"fields.{name}": CEL_TYPES_MAP.get(field["store"].get_python_type(), Type.DYN)
            for name, field in fields_def.items()
        }
    )
    errors = {}
    for name, field in fields_def.items():
        store = field["store"]
        widget = field.get("widget")
        expressions = {
            "required_cel": [store.required_cel] if store.required_cel is not None else [],
            "validate_cel": [condition["condition"] for condition in store.validate_cel or []],
            "hidden_cel": (
                [widget.get("hidden_cel")] if widget and widget.get("hidden_cel") else []
            ),
        }
        for key, conditions in expressions.items():
            for expression in conditions:
                try:
                    check_cel_type(env, expression)
                except ValidationError as e:
                    errors.setdefault(name, {}).setdefault(key, []).extend(e.messages)
    entity_errors = []
    for condition in entity_validate_cel or []:
        try:
            check_cel_type(env, condition["condition"])
        except ValidationError as e:
            entity_errors.extend(e.messages)
    if errors or entity_errors:
        raise ValidationError(
            {
                **({"fields": errors} if errors else {}),
                **({"validate_cel": entity_errors} if entity_errors else {}),
            }
        )


class ExportPdfSchema(ma.Schema):
    class Meta:
        unknown = ma.RAISE

    label = ma.fields.Str(required=True)
    template = ma.fields.Str(required=True)


class BaseEntityConfigSchema(ma.Schema):
    class Meta:
        unknown = ma.RAISE

    fields = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Nested(EntityFieldConfigSchema))
    display_properties = ma.fields.List(ma.fields.Str(), load_default=[])
    display_list = ma.fields.List(ma.fields.Str())
    # Clés descriptives utilisées par le frontend : conservées telles quelles si présentes
    # (pas de load_default, pour ne pas ajouter de clé absente de la config legacy)
    chained = ma.fields.Raw()
    change = ma.fields.Raw()
    # Filtres par défaut appliqués à la liste de l’objet : {nom_du_champ: valeur ou liste de valeurs}
    # (ex. {"active": True} ou {"cd_nomenclature": ["1", "2"]}).
    # Lu par le frontend (monitoring-geom-component.ts : defaultFilters) et par sites-groups.resolver.ts.
    filters = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Raw())
    genre = ma.fields.Str()
    geom_field_name = ma.fields.Str()
    geometry_type = ma.fields.Raw()
    id_field_name = ma.fields.Str()
    description_field_name = ma.fields.Str()
    label = ma.fields.Str()
    label_list = ma.fields.Str()
    # Liste des champs (noms de fields) dont la dernière valeur saisie est conservée
    # par le formulaire après la création d’un objet (ex. ["id_dataset", "observers"]).
    # Lu par monitoring-form-g.component.ts (resetForm / clé "keep").
    keep = ma.fields.List(ma.fields.Str())
    # Modèles de rapports PDF proposés pour l’objet. Liste d’objets {label, template}.
    # Lu par monitoring-geom-component.ts (templateData.exportPDF) pour afficher le bouton
    # d’export PDF dans monitoring-properties-g.component.html.
    export_pdf = ma.fields.List(ma.fields.Nested(ExportPdfSchema))
    sorts = ma.fields.Raw()
    uuid_field_name = ma.fields.Str()
    # Condition CEL sur l’objet entier, évaluée par le schéma (voir CELMixin)
    validate_cel = CELValidationsField()
    # Calculés à partir de l’arbre du module (voir load_tree_relations)
    parent_types = ma.fields.List(ma.fields.Str(), dump_only=True)
    children_types = ma.fields.List(ma.fields.Str(), dump_only=True)

    @pre_load
    def pre_load(self, data, **kwargs):
        """
        Ce hook s’occupe de merger la config par défaut avec la config que l’on s’apprête à charger.
        """
        substitutions = schema_context.get()["entity"].module.substitutions
        data = apply_substitutions(data, substitutions)
        # Permet de valider de manière minimale les fields pour les manipuler
        fields_field = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Dict())
        # specific is a retro.compat key
        fields = data.pop("fields", data.pop("specific", {}))
        fields = fields_field.deserialize(fields)
        # On écrase tous les champs, sauf "fields" qui a été sortie
        # TODO: et sauf validate_cel pour lequel on doit étendre la liste ?
        data = {**apply_substitutions(self.get_default_config(), substitutions), **data}
        # Comme le legacy : display_list vaut display_properties si non défini
        data.setdefault("display_list", data.get("display_properties", []))
        # Maintenant, pour les fields, on permet :
        #   - de définir de nouveau fields, s’ils n’existent pas en base
        #   - d’override, pour les fields existant dans default_data, uniquement :
        #     - le widget
        #     - required, seulement si c’est pour le forcer à True
        model = schema_context.get()["entity"].model
        mapper = sa.inspect(model)
        for field_name, field_def in fields.items():
            if field_name in data["fields"]:  # field existant
                # TODO: restreindre l’override pour interdire de modifier le type des champs sql !
                data["fields"][field_name].update(field_def)
            else:  # nouveau field, on l’ajoute
                if field_name in mapper.attrs:
                    raise ValidationError(
                        {
                            "fields": {
                                field_name: "Ce champs rentre en conflit avec un champs du modèle."
                            }
                        }
                    )
                data["fields"][field_name] = field_def

        # On rajoute à chaque field une clé "name" pour que chaque field est connaissance de son nom
        data["fields"] = {k: {**v, "name": k} for k, v in data["fields"].items()}
        return data

    @validates_schema
    def validates_schema(self, data, **kwargs):
        schema = schema_context.get()["entity"].get_model_schema()
        for field in data["display_list"]:
            if field not in data["fields"] and not hasattr(schema, field):
                raise ValidationError({"display_list": f"Le champs '{field}' n’a pas été défini."})
        for field in data["display_properties"]:
            if field not in data["fields"] and not hasattr(schema, field):
                raise ValidationError(
                    {"display_properties": f"Le champs '{field}' n’a pas été défini."}
                )
        check_cel_types(data["fields"], data.get("validate_cel"))

    @post_load
    def load_tree_relations(self, data, **kwargs):
        """
        Ajoute `parent_types` et `children_types` : les types d’objets parents et enfants directs
        de cette entité dans l’arbre du module.
        """
        entity = schema_context.get()["entity"]
        parent_types = []
        children_types = []

        def walk(subtree, parent_type=None):
            for object_type, sub in (subtree or {}).items():
                if object_type == entity.name:
                    if parent_type:
                        parent_types.append(parent_type)
                    children_types.extend((sub or {}).keys())
                walk(sub, object_type)

        walk(entity.module["tree"])
        data["parent_types"] = list(dict.fromkeys(parent_types))
        data["children_types"] = list(dict.fromkeys(children_types))
        return data

    def get_default_config(self):
        return deepcopy(self.default_config)
