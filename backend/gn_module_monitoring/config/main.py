import json

import sqlalchemy as sa
from flask import current_app
from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    RAISE,
    INCLUDE,
    validates_schema,
    pre_load,
    post_load,
)

from geonature.utils.env import db
from pypnusershub.db.models import UserList

from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.config.utils import (
    get_monitorings_path,
    get_tree_relations,
    monitoring_module_config_path,
)


class ObservationDetailTreeSchema(Schema):
    class Meta:
        unknown = RAISE


class ObservationTreeSchema(Schema):
    class Meta:
        unknown = RAISE

    observation_detail = fields.Nested(ObservationDetailTreeSchema, allow_none=True)


class VisitTreeSchema(Schema):
    class Meta:
        unknown = RAISE

    observation = fields.Nested(ObservationTreeSchema, allow_none=True)


class SiteTreeSchema(Schema):
    class Meta:
        unknown = RAISE

    visit = fields.Nested(VisitTreeSchema, allow_none=True)


class SiteGroupTreeSchema(Schema):
    class Meta:
        unknown = RAISE

    site = fields.Nested(SiteTreeSchema, allow_none=True)


class MarkingTreeSchema(Schema):
    class Meta:
        unknown = RAISE


class IndividualTreeSchema(Schema):
    class Meta:
        unknown = RAISE

    marking = fields.Nested(MarkingTreeSchema, allow_none=True)


class ModuleTreeSchema(Schema):
    class Meta:
        unknown = RAISE

    sites_group = fields.Nested(SiteGroupTreeSchema)
    site = fields.Nested(SiteTreeSchema, allow_none=True)
    individual = fields.Nested(IndividualTreeSchema, allow_none=True)

    @validates_schema
    def validate_schema(self, data, **kwarsg):
        if not data.get("site") and not data.get("sites_group") and not data.get("individual"):
            raise ValidationError("At least one of site or sites_group or individual required.")


class TreeSchema(Schema):
    class Meta:
        unknown = RAISE

    module = fields.Nested(ModuleTreeSchema, required=True)


class DataSchema(Schema):
    class Meta:
        unknown = INCLUDE  # this schema in incomplete


class ModuleConfigSchema(Schema):
    class Meta:
        unknown = RAISE

    tree = fields.Nested(
        TreeSchema,
        load_default={
            "module": {
                "sites_group": {"site": {"visit": {"observation": {"observation_detail": None}}}},
                "site": None,
            }
        },
    )
    synthese_object = fields.String(validate=validate.OneOf(["observation", "visit"]))
    display_field_names = fields.Dict()
    data = fields.Nested(DataSchema)

    @pre_load
    def remove_deprecated(self, data, **kwargs):
        """
        This hook trash deprecated fields data, avoiding raising unexpected fields errors.
        """
        data.pop("permission_objects", None)  # supprimé dans la 0.7.0
        return data

    @post_load
    def load_tree_relations(self, data, **kwargs):
        """
        Ajoute `parent_types` et `children_types` (dict type d'objet -> liste de types),
        calculés à partir de `tree`.
        """
        data["parent_types"], data["children_types"] = get_tree_relations(data.get("tree", {}))
        return data


def load_module_root_config(module_code):
    """
    Charge la config de base depuis config.json.

    Raises:
        UnicodeDecodeError
        JSONDecodeError
        ValidationError
    """
    # Validation marshmallow
    if module_code == "generic":
        config = {}
    else:
        config_path = monitoring_module_config_path(module_code) / "config.json"
        config = json.loads(config_path.read_text())
    with schema_context(module_code=module_code):
        config = ModuleConfigSchema().load(config)
    return config


def load_module_db_config(module):
    module_config = {
        attr: getattr(module, attr)
        for attr in [
            "module_code",
            "id_list_taxonomy",
            "b_synthese",
            "b_draw_sites_group",
            "taxonomy_display_field_name",
            "id_module",
            "cd_nom",
        ]
    }
    if module.id_list_observer:
        module_config["code_observers_list"] = db.session.execute(
            sa.select(UserList.code_liste).where(UserList.id_liste == module.id_list_observer)
        ).scalar_one()
    else:
        module_config["code_observers_list"] = current_app.config["MONITORINGS"][
            "CODE_OBSERVERS_LIST"
        ]
    return module_config
