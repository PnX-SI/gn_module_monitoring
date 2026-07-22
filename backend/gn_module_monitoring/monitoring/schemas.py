from geonature.core.gn_monitoring.models import TBaseSites
import geojson

from flask import g
from marshmallow import Schema, fields, validate, pre_load, ValidationError

import marshmallow

from geonature.utils.env import MA
from geonature.core.gn_commons.schemas import MediaSchema, ModuleSchema
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.gn_meta.schemas import DatasetSchema
from geonature.utils.schema import CruvedSchemaMixin
from marshmallow_sqlalchemy import auto_field
from pypnusershub.db.models import User

from utils_flask_sqla_geo.utilsgeometry import remove_third_dimension
from shapely.geometry import shape
from geoalchemy2.shape import to_shape, from_shape
from geojson import Feature

from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringSitesGroups,
    TMonitoringVisits,
    TMonitoringModules,
    TMonitoringObservations,
    TMonitoringObservationDetails,
    TMonitoringIndividuals,
)


def paginate_schema(schema):
    class PaginationSchema(Schema):
        count = fields.Integer()
        limit = fields.Integer()
        page = fields.Integer()
        items = fields.Nested(schema, many=True, dump_only=True)

    return PaginationSchema


def add_specific_attributes(schema, object_type, module_code):
    """Crée une classe Schema dynamiquement pour ajouter les propriétés spécifiques du type d'objet
    à la classe 'schema' passée en argument."""

    # FIXME: déplacer ces imports hors de la fonction mais il faut résoudre un pb de circular import
    from gn_module_monitoring.config.repositories import get_config
    from gn_module_monitoring.monitoring.definitions import (
        MonitoringModels_dict,
        MonitoringObjects_dict,
    )
    from gn_module_monitoring.monitoring.geom import MonitoringObjectGeom
    from gn_module_monitoring.config.utils import get_specific_properties

    model_class = MonitoringModels_dict[object_type]

    config = get_config(module_code)

    specific_properties = get_specific_properties(model_class, config, object_type).keys()

    def create_getter(key):
        return lambda obj: (obj.data or {}).get(key)

    attrs = {}
    for property_ in specific_properties:
        attrs[property_] = marshmallow.fields.Function(create_getter(property_))

    monitoring_object_class = MonitoringObjects_dict[object_type]
    parameters = {"model": model_class, "exclude": ["data"], "include_fk": True}
    if issubclass(monitoring_object_class, MonitoringObjectGeom):
        parameters["exclude"].extend(["geom_geojson", "geom"])
    if issubclass(model_class, TBaseSites):
        parameters["exclude"].extend(["geom_local"])
    Meta = type("Meta", (), parameters)

    attrs.update({"Meta": Meta})
    schema_with_specifics = type(
        f"{object_type.capitalize()}SchemaWithSpecifics",
        (schema,),
        attrs,
    )
    return schema_with_specifics


class MonitoringCruvedSchemaMixin(CruvedSchemaMixin):

    @property
    def __module_code__(self):
        if not getattr(g, "current_module", None):
            return None
        return g.current_module.module_code


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

    pk = fields.Method("set_pk", dump_only=True)

    def set_pk(self, obj):
        return "id_module"


# PATCH : To move in utils_flask_sqla_geo
class GeojsonSerializationField(fields.Field):

    def _serialize(self, value, attr, obj):
        if value is None:
            return value
        else:
            if type(value).__name__ == "WKBElement":
                feature = Feature(geometry=to_shape(value))
                return feature.geometry
            else:
                return None

    def _deserialize(self, value, attr, data, **kwargs):
        if not value:
            return None
        try:
            shape_ = shape(value)
            two_dimension_geom = remove_third_dimension(shape_)
            return from_shape(two_dimension_geom, srid=4326)
        except Exception as error:
            raise ValidationError("Geometry error") from error


class MonitoringSitesGroupsSchema(MA.SQLAlchemyAutoSchema):

    class Meta:
        model = TMonitoringSitesGroups
        load_instance = True
        include_fk = True
        load_relationships = True
        exclude = ("geom_geojson",)

    sites_group_name = fields.String(
        validate=validate.Length(min=3, error="Length must be greater than 3"),
    )
    id_sites_group = auto_field(allow_none=True)
    medias = MA.Nested(MediaSchema, many=True)
    pk = fields.Method("set_pk", dump_only=True)
    is_geom_from_child = fields.Method("set_is_geom_from_child", dump_only=True)
    modules = MA.Pluck(ModuleSchema, "id_module", many=True)
    nb_visits = fields.Integer(dump_only=True)
    geom = GeojsonSerializationField(required=False, allow_none=True)

    def set_pk(self, obj):
        return "id_sites_group"

    def set_is_geom_from_child(self, obj):
        if obj.geom is None and obj.geom_geojson is None:
            return True
        if obj.geom is not None:
            return False
        if obj.geom_geojson is not None:
            return True

    @pre_load
    def normalize(self, data, **kwargs):
        data["medias"] = data.get("medias") or []
        return data


class MonitoringSitesGroupsSchemaCruved(MonitoringCruvedSchemaMixin, MonitoringSitesGroupsSchema):
    pass


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
        exclude = ("geom_geojson", "geom", "geom_local")
        include_fk = True
        load_relationships = True

    geometry = fields.Method("serialize_geojson", dump_only=True)
    pk = fields.Method("set_pk", dump_only=True)
    types_site = MA.Nested(BibTypeSiteSchema, many=True)
    id_sites_group = fields.Method("get_id_sites_group")
    id_inventor = fields.Method("get_id_inventor")
    medias = MA.Nested(MediaSchema, many=True)
    nb_visits = fields.Integer(dump_only=True)
    last_visit = fields.Date(dump_only=True)
    first_use_date = fields.Date(dump_only=True)

    def serialize_geojson(self, obj):
        if obj.geom is not None:
            return geojson.dumps(obj.as_geofeature().get("geometry"))

    def set_pk(self, obj):
        return "id_base_site"

    def get_id_sites_group(self, obj):
        return obj.id_sites_group

    def get_id_inventor(self, obj):
        return obj.id_inventor


class MonitoringSitesSchemaCruved(MonitoringCruvedSchemaMixin, MonitoringSitesSchema):
    pass


class MonitoringVisitsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringVisits
        include_fk = True
        load_relationships = True

    pk = fields.Method("set_pk", dump_only=True)
    module = MA.Nested(ModuleSchema)
    medias = MA.Nested(MediaSchema, many=True)
    visit_date_min = MA.Date()
    visit_date_max = MA.Date()

    observers = MA.Pluck(ObserverSchema, "id_role", many=True)

    def set_pk(self, obj):
        return "id_base_visit"


class MonitoringVisitsSchemaCruved(MonitoringCruvedSchemaMixin, MonitoringVisitsSchema):
    pass


class MonitoringObservationsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringObservations
        include_fk = True
        load_relationships = True

    medias = MA.Nested(MediaSchema, many=True)


class MonitoringObservationsSchemaCruved(
    MonitoringCruvedSchemaMixin, MonitoringObservationsSchema
):
    pass


class MonitoringObservationsDetailsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringObservationDetails
        include_fk = True
        load_relationships = True

    medias = MA.Nested(MediaSchema, many=True)


class MonitoringObservationsDetailsSchemaCruved(
    MonitoringCruvedSchemaMixin, MonitoringObservationsDetailsSchema
):
    pass


class MonitoringIndividualsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringIndividuals
        include_fk = True
        load_relationships = True

    medias = MA.Nested(MediaSchema, many=True)

    pk = fields.Method("set_pk", dump_only=True)

    def set_pk(self, obj):
        return "id_individual"


class MonitoringIndividualsSchemaCruved(MonitoringCruvedSchemaMixin, MonitoringIndividualsSchema):
    pass
