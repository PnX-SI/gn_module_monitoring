from copy import deepcopy

import sqlalchemy as sa
import marshmallow as ma
from marshmallow import pre_load, validates_schema, ValidationError

from gn_module_monitoring.config.utils import customize_config, get_data_preload
from .fields import EntityFieldConfigSchema, schema_context


class BaseEntityConfigSchema(ma.Schema):
    class Meta:
        # TODO: le but est de passer à RAISE une fois les schémas complets
        unknown = ma.EXCLUDE

    fields = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Nested(EntityFieldConfigSchema))
    display_list = ma.fields.List(ma.fields.Str(), load_default=[])
    display_properties = ma.fields.List(ma.fields.Str(), load_default=[])

    def __init__(self, *, module_tree, **kwargs) -> None:
        super().__init__(**kwargs)
        self.module_tree = module_tree

    @pre_load
    def pre_load(self, data, **kwargs):
        """
        Ce hook s’occupe de merger la config generic avec la config specific.
        Il s’occupe également de la customisation (remplacement des chaînes spétial __MODULE.…).
        """
        customize_config(data, get_data_preload(data))
        # Permet de valider de manière minimale les fields pour les manipuler
        fields_field = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Dict())
        # specific is a retro.compat key
        fields = data.pop("fields", data.pop("specific", {}))
        fields = fields_field.deserialize(fields)
        # On écrase tous les champs, sauf "fields" qui a été sortie
        data = {**self.get_default_config(), **data}
        # Maintenant, pour les fields, on permet :
        #   - de définir de nouveau fields, s’ils n’existent pas en base
        #   - d’override, pour les fields existant dans default_data, uniquement :
        #     - le widget
        #     - required, seulement si c’est pour le forcer à True
        model = schema_context.get()["entity_service"].model
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
        for field in data["display_list"]:
            if field not in data["fields"]:
                raise ValidationError({"display_list": f"Le champs '{field}' n’a pas été défini."})
        for field in data["display_properties"]:
            if field not in data["fields"]:
                raise ValidationError(
                    {"display_properties": f"Le champs '{field}' n’a pas été défini."}
                )

    def get_default_config(self):
        return deepcopy(self.default_config)
