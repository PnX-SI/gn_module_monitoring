from typing import ClassVar

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    RAISE,
    INCLUDE,
    validates_schema,
    pre_load,
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
    # Active la synchronisation de la synthèse (`process_synthese`, route `synthese/<module_code>`).
    # Copie de `TMonitoringModules.b_synthese` (rétro-compatibilité avec la config v2).
    synthese = fields.Boolean(attribute="module.b_synthese", dump_only=True)
    synthese_object = fields.String(validate=validate.OneOf(["observation", "visit"]))
    display_field_names = fields.Dict()
    data = fields.Nested(DataSchema)
    configured = fields.Boolean(dump_only=True)

    default_display_field_names: ClassVar = {
        "user": "nom_complet",
        "nomenclature": "label_fr",
        "dataset": "dataset_name",
        "observer_list": "nom_liste",
        "taxonomy": "__MODULE.TAXONOMY_DISPLAY_FIELD_NAME",
        "taxonomy_list": "nom_liste",
        "cd_nom": "cd_nom",
        "sites_group": "sites_group_name",
        "habitat": "lb_hab_fr",
        "area": "area_name",
        "municipality": "nom_com_dept",
        "site": "base_site_name",
        "module": "module_label",
    }

    @pre_load
    def remove_deprecated(self, data, **kwargs):
        """
        This hook trash deprecated fields data, avoiding raising unexpected fields errors.
        """
        data.pop("permission_objects", None)  # supprimé dans la 0.7.0
        return data

    @pre_load
    def merge_display_field_names(self, data, **kwargs):
        """
        Surcharge les noms d’affichage par défaut par ceux du module, clé par clé.
        """
        data["display_field_names"] = {
            **self.default_display_field_names,
            **data.get("display_field_names", {}),
        }
        return data
