import datetime
import uuid
from copy import deepcopy

import sqlalchemy as sa
import marshmallow as ma
from cel_expr_python.cel import NewEnv, Type
from marshmallow import pre_load, post_load, validates_schema, ValidationError

from gn_module_monitoring.config.utils import apply_substitutions
from gn_module_monitoring.tools.utils import (
    CELValidationsField,
    MultilineStr,
    compile_cel_expression,
)
from .fields import EntityFieldConfigSchema, schema_context

# Types CEL des valeurs Python des stores (par type Python de la valeur chargée) :
CEL_TYPES_MAP = {
    int: Type.INT,
    float: Type.DOUBLE,
    bool: Type.BOOL,
    str: Type.STRING,
    uuid.UUID: Type.STRING,  # converti en chaîne pour CEL
    datetime.date: Type("google.protobuf.Timestamp"),
    datetime.datetime: Type("google.protobuf.Timestamp"),
}


def cel_variable_type(store):
    """
    Type CEL de la variable `fields.<nom>`. Seul un scalaire `required` statique a un type :
    marshmallow refuse une valeur absente ou nulle avant l’évaluation des conditions. Les autres
    champs peuvent être vides (None) : ils sont déclarés `DYN`, et leur typage n’est pas vérifié.
    """
    if store.required is True:
        return CEL_TYPES_MAP.get(store.get_python_type(), Type.DYN)
    return Type.DYN


def build_cel_env(fields_def):
    """
    Environnement CEL d’une entité : une variable `fields.<nom>` par champ. Construit une seule
    fois par chargement de l’entité, et transmis à chaque champ en argument.
    """
    return NewEnv(
        variables={
            f"fields.{name}": cel_variable_type(field["store"])
            for name, field in fields_def.items()
        }
    )


def compile_field_cel_expressions(field, env):
    """
    Compile les expressions CEL d’un champ (`required_cel`, `validate_cel`, `hidden_cel`) avec
    l’environnement de l’entité, et les stocke dans le champ :
    `compiled_required_cel`, `compiled_validate_cel` [(expression, message)] et
    `compiled_hidden_cel`.

    Lève ValidationError, avec une clé par type d’expression, si une expression est invalide.
    """
    errors = {}

    def compile_one(key, expression):
        try:
            return compile_cel_expression(env, expression)
        except ValidationError as e:
            errors.setdefault(key, []).extend(e.messages)

    store = field["store"]
    field["compiled_required_cel"] = (
        compile_one("required_cel", store.required_cel) if store.required_cel is not None else None
    )
    field["compiled_validate_cel"] = []
    for condition in store.validate_cel or []:
        expression = compile_one("validate_cel", condition["condition"])
        if expression is not None:
            field["compiled_validate_cel"].append((expression, condition["message"]))
    hidden_cel = (field.get("widget") or {}).get("hidden_cel")
    field["compiled_hidden_cel"] = compile_one("hidden_cel", hidden_cel) if hidden_cel else None
    if errors:
        raise ValidationError(errors)


def compile_entity_cel_expressions(data):
    """
    Compile les expressions CEL d’une entité chargée (`fields`, `validate_cel`).

    - chaque champ reçoit ses expressions compilées (voir compile_field_cel) ;
    - l’entité reçoit `compiled_validate_cel` : [(expression compilée, message)].

    Les erreurs sont regroupées comme la validation de la configuration : par champ sous
    `fields`, et pour l’entité sous `validate_cel`.
    """
    env = build_cel_env(data["fields"])
    errors = {}
    for name, field in data["fields"].items():
        try:
            compile_field_cel_expressions(field, env)
        except ValidationError as e:
            errors.setdefault("fields", {})[name] = e.messages
    data["compiled_validate_cel"] = []
    for condition in data.get("validate_cel") or []:
        try:
            expression = compile_cel_expression(env, condition["condition"])
        except ValidationError as e:
            errors.setdefault("validate_cel", []).extend(e.messages)
        else:
            data["compiled_validate_cel"].append((expression, condition["message"]))
    if errors:
        raise ValidationError(errors)
    return data


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
    chained = ma.fields.Boolean()
    # Lu par le frontend (monitoring-form-g.component.ts) après enregistrement, pour toutes les entités
    redirect_to_parent = ma.fields.Boolean()
    change = MultilineStr()
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
        # FIXME: we should validate specific & fields are dict … or better: just drop specific handling …
        fields = {**data.pop("specific", {}), **data.pop("fields", {})}
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
            if field not in data["fields"] and field not in schema.fields:
                raise ValidationError({"display_list": f"Le champs '{field}' n’a pas été défini."})
        for field in data["display_properties"]:
            if field not in data["fields"] and field not in schema.fields:
                raise ValidationError(
                    {"display_properties": f"Le champs '{field}' n’a pas été défini."}
                )

    @post_load
    def compile_cel(self, data, **kwargs):
        # Compilation unique des expressions CEL, réutilisée à l’évaluation (voir CELMixin)
        return compile_entity_cel_expressions(data)

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
