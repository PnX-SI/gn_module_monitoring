import json

from marshmallow import Schema, ValidationError, fields, validate, RAISE, validates_schema

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.config.repositories import get_config


class ObservationDetailTreeSchema(Schema):
    pass


class ObservationTreeSchema(Schema):
    observation_detail = fields.Nested(ObservationDetailTreeSchema, allow_none=True)


class VisitTreeSchema(Schema):
    observation = fields.Nested(ObservationTreeSchema, allow_none=True)


class SiteTreeSchema(Schema):
    visit = fields.Nested(VisitTreeSchema, allow_none=True)


class SiteGroupTreeSchema(Schema):
    site = fields.Nested(SiteTreeSchema, allow_none=True)


class ModuleTreeSchema(Schema):
    sites_group = fields.Nested(SiteGroupTreeSchema)
    site = fields.Nested(SiteTreeSchema, allow_none=True)

    @validates_schema
    def validate_schema(self, data, **kwarsg):
        if not data.get("site") and not data.get("sites_group"):
            raise ValidationError("At least one of site or sites_group is required.")


class TreeSchema(Schema):
    module = fields.Nested(ModuleTreeSchema, required=True)


class DataSchema(Schema):
    pass


class ModuleConfigSchema(Schema):
    tree = fields.Nested(TreeSchema)
    synthese_object = fields.String(validate=validate.OneOf(["observation"]))
    permission_objects = fields.List(  # FIXME: Legacy
        fields.String(
            validate=validate.OneOf(
                ["GNM_GRP_SITES", "GNM_SITES", "GNM_VISITES", "GNM_OBSERVATIONS"]
            )
        )
    )
    display_field_names = fields.Dict()
    data = fields.Nested(DataSchema)


def check_module_config(module_code):
    config_path = monitoring_module_config_path(module_code) / "config.json"
    config = json.loads(config_path.read_text())
    try:
        ModuleConfigSchema().load(
            config,
            unknown=RAISE,
        )
    except ValidationError as e:
        yield e

    # La fonction get_config va également enrichir celle-ci pour obtenir une configuration opérationelle
    # Cependant, le chargement du fichier n’est pas validé par un schéma, d’où notre contrôle précédent.
    try:
        config = get_config(module_code, force=True)
    except Exception as e:  # FIXME: revoir get_config pour éviter les exceptions
        yield e
        return
    return config
