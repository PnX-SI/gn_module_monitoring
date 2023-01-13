import json

import geojson
from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from pypnnomenclature.schemas import NomenclatureSchema

from gn_module_monitoring.monitoring.models import (
    BibTypeSite,
    TMonitoringSites,
    TMonitoringSitesGroups,
)


def paginate_schema(schema):
    class PaginationSchema(Schema):
        count = fields.Integer()
        limit = fields.Integer()
        offset = fields.Integer()
        items = fields.Nested(schema, many=True, dump_only=True)

    return PaginationSchema


class MonitoringSitesGroupsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringSitesGroups
        exclude = ("geom_geojson",)

    geometry = fields.Method("serialize_geojson", dump_only=True)

    def serialize_geojson(self, obj):
        if obj.geom_geojson is not None:
            return json.loads(obj.geom_geojson)


class MonitoringSitesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringSites
        exclude = ("geom_geojson", "geom")

    geometry = fields.Method("serialize_geojson", dump_only=True)

    def serialize_geojson(self, obj):
        if obj.geom is not None:
            return geojson.dumps(obj.as_geofeature().get("geometry"))


class BibTypeSiteSchema(SQLAlchemyAutoSchema):
    label = fields.Method("get_label_from_type_site")
    # See if useful in the future:
    # type_site = fields.Nested(NomenclatureSchema(only=("label_fr",)), dump_only=True)

    def get_label_from_type_site(self, obj):
        return obj.nomenclature.label_fr

    class Meta:
        model = BibTypeSite
        include_fk = True
        load_instance = True
