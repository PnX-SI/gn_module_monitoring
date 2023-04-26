import json

import geojson
from geonature.utils.env import MA
from marshmallow import Schema, fields, validate
from geonature.core.gn_commons.schemas import MediaSchema, ModuleSchema

from gn_module_monitoring.monitoring.models import (
    BibTypeSite,
    TMonitoringSites,
    TMonitoringSitesGroups,
    TMonitoringVisits,
)


def paginate_schema(schema):
    class PaginationSchema(Schema):
        count = fields.Integer()
        limit = fields.Integer()
        page = fields.Integer()
        items = fields.Nested(schema, many=True, dump_only=True)

    return PaginationSchema


class MonitoringSitesGroupsSchema(MA.SQLAlchemyAutoSchema):
    
    sites_group_name = fields.String(
        validate=validate.Length(min=3,error="Length must be greater than 3"),)
        
    class Meta:
        model = TMonitoringSitesGroups
        exclude = ("geom_geojson",)
        load_instance = True

    medias = MA.Nested(MediaSchema,many=True)
    pk = fields.Method("set_pk",dump_only=True)
    geometry = fields.Method("serialize_geojson", dump_only=True)
    
    def set_pk(self,obj):
        return self.Meta.model.get_id()

    def serialize_geojson(self, obj):
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

    geometry = fields.Method("serialize_geojson", dump_only=True)
    pk = fields.Method("set_pk",dump_only=True)
    types_site = MA.Nested(BibTypeSiteSchema, many=True)

    def serialize_geojson(self, obj):
        if obj.geom is not None:
            return geojson.dumps(obj.as_geofeature().get("geometry"))
        
    def set_pk(self,obj):
        return self.Meta.model.get_id()

class MonitoringVisitsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringVisits
    pk = fields.Method("set_pk",dump_only=True)
    module = MA.Nested(ModuleSchema)

    def set_pk(self,obj):
        return self.Meta.model.get_id()
