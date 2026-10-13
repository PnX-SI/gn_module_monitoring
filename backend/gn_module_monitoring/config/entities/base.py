import marshmallow as ma
from marshmallow import pre_load, validates_schema, ValidationError

from .fields import EntityFieldConfigSchema


class BaseEntityConfigSchema(ma.Schema):
    class Meta:
        # TODO: le but est de passer à RAISE une fois les schémas complets
        unknown = ma.EXCLUDE

    fields = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Nested(EntityFieldConfigSchema))
    # fields = ma.fields.List(ma.fields.Nested(EntityFieldConfigSchema))
    display_list = ma.fields.List(ma.fields.Str(), load_default=[])
    display_properties = ma.fields.List(ma.fields.Str(), load_default=[])

    @pre_load
    def pre_load(self, data, **kwargs):
        """
        Ce hook s’occupe de merger la config generic avec la config specific.
        """
        # Permet de valider de manière minimale les fields pour les manipuler
        fields_field = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Dict())
        # specific is a retro.compat key
        fields = data.pop("fields", data.pop("specific", {}))
        fields = fields_field.deserialize(fields)
        # On écrase tous les champs, sauf "fields" qui a été sortie
        data = {**self.base_data, **data}
        # Maintenant, pour les fields, on permet :
        #   - de définir de nouveau fields
        #   - d’override, pour les fields existant dans default_data, uniquement :
        #     - le widget
        #     - required, seulement si c’est pour le forcer à True
        for field_name, field_def in fields.items():
            if field_name in data["fields"]:  # field existant
                # TODO: Comportement legacy, adopter le comportement strict décrit ci-dessus
                data["fields"][field_name].update(field_def)
            else:  # nouveau field, on l’ajoute
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
