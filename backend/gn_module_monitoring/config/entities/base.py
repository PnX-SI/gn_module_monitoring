from copy import deepcopy

import sqlalchemy as sa
import marshmallow as ma
from marshmallow import pre_load, post_load, validates_schema, ValidationError

from gn_module_monitoring.config.utils import apply_substitutions
from gn_module_monitoring.tools.utils import CELValidationsField
from .fields import EntityFieldConfigSchema, schema_context


class BaseEntityConfigSchema(ma.Schema):
    class Meta:
        # TODO: le but est de passer à RAISE une fois les schémas complets
        unknown = ma.EXCLUDE

    fields = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Nested(EntityFieldConfigSchema))
    display_properties = ma.fields.List(ma.fields.Str(), load_default=[])
    display_list = ma.fields.List(ma.fields.Str())
    # Clés descriptives utilisées par le frontend : conservées telles quelles si présentes
    # (pas de load_default, pour ne pas ajouter de clé absente de la config legacy)
    chained = ma.fields.Raw()
    change = ma.fields.Raw()
    filters = ma.fields.Raw()
    genre = ma.fields.Str()
    geom_field_name = ma.fields.Str()
    geometry_type = ma.fields.Raw()
    id_field_name = ma.fields.Str()
    description_field_name = ma.fields.Str()
    label = ma.fields.Str()
    label_list = ma.fields.Str()
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
