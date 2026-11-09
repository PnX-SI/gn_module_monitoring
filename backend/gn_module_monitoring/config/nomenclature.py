import json

from marshmallow import Schema, fields, post_load

from geonature.utils.env import ma
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.config.utils import monitoring_module_config_path


class NomenclatureTypeDefinitionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BibNomenclaturesTypes
        exclude = ("id_type",)

    @post_load
    def set_default(self, data, **kwargs):
        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"
        return data


class NomenclatureDefinitionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TNomenclatures
        exclude = ("id_type", "id_nomenclature")

    type = fields.String()
    active = ma.auto_field(dump_only=True, load_default=True)

    @post_load
    def set_default(self, data, **kwargs):
        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"
        return data


class NomenclaturesDefinitionSchema(Schema):
    types = fields.List(fields.Nested(NomenclatureTypeDefinitionSchema), load_default=[])
    nomenclatures = fields.List(fields.Nested(NomenclatureDefinitionSchema), load_default=[])


def load_module_nomenclatures(module_code):
    nomenclatures_path = monitoring_module_config_path(module_code) / "nomenclature.json"
    if nomenclatures_path.is_file():
        with nomenclatures_path.open() as f:
            nomenclatures = json.load(f)
    else:
        nomenclatures = {}
    return NomenclaturesDefinitionSchema().load(nomenclatures)
