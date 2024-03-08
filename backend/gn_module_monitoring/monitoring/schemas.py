import json
import geojson

from marshmallow import Schema, fields, validate

from geonature.utils.env import MA
from geonature.core.gn_commons.schemas import MediaSchema, ModuleSchema
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.gn_meta.schemas import DatasetSchema

from pypnusershub.db.models import User


from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringSitesGroups,
    TMonitoringVisits,
    TMonitoringModules,
    TMonitoringObservations,
    TMonitoringObservationDetails,
)


def paginate_schema(schema):
    class PaginationSchema(Schema):
        count = fields.Integer()
        limit = fields.Integer()
        page = fields.Integer()
        items = fields.Nested(schema, many=True, dump_only=True)

    return PaginationSchema


class ObserverSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = (
            "_password",
            "_password_plus",
            "active",
            "date_insert",
            "date_update",
            "desc_role",
            "email",
            "groupe",
            "remarques",
            "identifiant",
        )

    nom_complet = fields.Str(dump_only=True)


class MonitoringBibTypeSiteSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = BibTypeSite
        include_fk = True


class MonitoringModuleSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringModules
        load_instance = True
        load_relationships = True
        include_fk = True
        # include_fk=True

    types_site = MA.Pluck(MonitoringBibTypeSiteSchema, "id_nomenclature_type_site", many=True)
    datasets = MA.Pluck(DatasetSchema, "id_dataset", many=True)
    medias = MA.Nested(MediaSchema, many=True)


class MonitoringSitesGroupsSchema(MA.SQLAlchemyAutoSchema):
    sites_group_name = fields.String(
        validate=validate.Length(min=3, error="Length must be greater than 3"),
    )

    class Meta:
        model = TMonitoringSitesGroups
        exclude = ("geom_geojson", "geom")
        load_instance = True
        include_fk = True
        load_relationships = True

    medias = MA.Nested(MediaSchema, many=True)
    pk = fields.Method("set_pk", dump_only=True)
    geometry = fields.Method("serialize_geojson", dump_only=True)
    id_digitiser = fields.Method("get_id_digitiser")
    is_geom_from_child = fields.Method("set_is_geom_from_child", dump_only=True)

    def get_id_digitiser(self, obj):
        return obj.id_digitiser

    def set_pk(self, obj):
        return "id_sites_group"

    def set_is_geom_from_child(self, obj):
        if obj.geom is None and obj.geom_geojson is None:
            return True
        if obj.geom is not None:
            return False
        if obj.geom_geojson is not None:
            return True

    def serialize_geojson(self, obj):
        if obj.geom is not None:
            return geojson.dumps(obj.as_geofeature().get("geometry"))
        if obj.geom_geojson is not None:
            return json.loads(obj.geom_geojson)


class BibTypeSiteSchema(MA.SQLAlchemyAutoSchema):
    label = fields.Method("get_label_from_type_site")
    # See if useful in the future:
    # type_site = fields.Nested(NomenclatureSchema(only=("label_fr",)), dump_only=True)

    def get_label_from_type_site(self, obj):
        return obj.nomenclature.label_fr

    class Meta:
        model = BibTypeSite
        include_fk = True
        load_instance = True


class MonitoringSitesSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringSites
        exclude = ("geom_geojson", "geom")
        include_fk = True
        load_relationships = True

    geometry = fields.Method("serialize_geojson", dump_only=True)
    pk = fields.Method("set_pk", dump_only=True)
    types_site = MA.Nested(BibTypeSiteSchema, many=True)
    id_sites_group = fields.Method("get_id_sites_group")
    observers = MA.Pluck(ObserverSchema, "id_role", many=True)
    medias = MA.Nested(MediaSchema, many=True)

    def serialize_geojson(self, obj):
        if obj.geom is not None:
            return geojson.dumps(obj.as_geofeature().get("geometry"))

    def set_pk(self, obj):
        return "id_base_site"

    def get_id_sites_group(self, obj):
        return obj.id_sites_group


class MonitoringVisitsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringVisits
        include_fk = True
        load_relationships = True

    pk = fields.Method("set_pk", dump_only=True)
    module = MA.Nested(ModuleSchema)
    medias = MA.Nested(MediaSchema, many=True)

    observers = MA.Pluck(ObserverSchema, "id_role", many=True)

    def set_pk(self, obj):
        return "id_base_visit"


class MonitoringObservationsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringObservations
        include_fk = True
        load_relationships = True


class MonitoringObservationsDetailsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringObservationDetails
        include_fk = True
        load_relationships = True
