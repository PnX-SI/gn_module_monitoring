import geojson
import json

from operator import attrgetter
from flask import g
import marshmallow
from geoalchemy2.shape import from_shape, to_shape
from geojson import Feature
from geonature.core.gn_commons.schemas import MediaSchema, ModuleSchema
from geonature.core.gn_monitoring.models import BibTypeSite, TBaseSites
from geonature.utils.env import MA
from geonature.utils.schema import CruvedSchemaMixin
from marshmallow import Schema, ValidationError, fields, post_dump, pre_load, validate
from marshmallow_sqlalchemy import auto_field
from marshmallow_sqlalchemy.fields import Related, RelatedList
from pypnusershub.db.models import User
from shapely.geometry import shape
from utils_flask_sqla_geo.utilsgeometry import remove_third_dimension

from gn_module_monitoring.monitoring.models import (
    TMonitoringIndividuals,
    TMonitoringModules,
    TMonitoringObservationDetails,
    TMonitoringObservations,
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

    config = get_config(module_code, force=True)
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


def generate_parents_schema(object_type):
    from gn_module_monitoring.monitoring.serializer import MonitoringSerializer_dict

    schema = MonitoringSerializer_dict[object_type]
    if g.current_module:
        schema = add_specific_attributes(schema, object_type, g.current_module.module_code)
    return schema


def generate_parents_data(hierarchy_list: [], obj) -> dict:
    parents = {}
    for element in hierarchy_list:
        obj_type = element.split(".")[-1]

        getter = attrgetter(element)
        attr = getter(obj)

        if attr:
            parent_schema = generate_parents_schema(obj_type)
            exclude = ("parents", "medias")
            valid_exclude = tuple(f for f in exclude if f in parent_schema._declared_fields)

            parents[obj_type] = generate_parents_schema(obj_type)(exclude=valid_exclude).dump(attr)
    return parents


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
        load_instance = True


class MonitoringModuleSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringModules
        load_instance = True
        load_relationships = True
        include_fk = True

    types_site = MA.Pluck(MonitoringBibTypeSiteSchema, "id_nomenclature_type_site", many=True)
    datasets = RelatedList(Related(["id_dataset"]))
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
            if isinstance(value, str):
                value = json.loads(value)
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
        exclude = ("geom_geojson", "geom_local", "parents")
        include_fk = True
        load_relationships = True
        load_instance = True

    id_base_site = auto_field(allow_none=True, required=False)
    pk = fields.Method("set_pk", dump_only=True)
    types_site = RelatedList(Related(["id_nomenclature_type_site"]))
    id_sites_group = fields.Method("get_id_sites_group")
    id_inventor = fields.Method("get_id_inventor")
    medias = MA.Nested(MediaSchema, many=True)
    nb_visits = fields.Integer(dump_only=True)
    last_visit = fields.Date(dump_only=True)
    first_use_date = fields.Date(dump_only=True)
    geom = GeojsonSerializationField()

    parents = fields.Method("get_parents", dump_only=True)

    def get_parents(self, obj):
        hierarchy_list = ["sites_group"]
        parents = generate_parents_data(hierarchy_list, obj)
        return parents

    def set_pk(self, obj):
        return "id_base_site"

    def get_id_sites_group(self, obj):
        return obj.id_sites_group

    def get_id_inventor(self, obj):
        return obj.id_inventor

    @pre_load
    def normalize(self, data, **kwargs):
        data["medias"] = data.get("medias") or []
        return data

    @post_dump
    def add_additional_fields(self, data, **kwargs):
        # Cas des propriétés renseignées dans d'autre module
        #  Ajout manuel des propriétés manquantes
        # TODO AJOUTER DES TESTS
        additional_fields_data = data.pop("data", {})
        if additional_fields_data is None:
            return data
        for key, value in additional_fields_data.items():
            if key not in data:
                data[key] = value
            if not data.get("additional_data_keys"):
                data["additional_data_keys"] = []
            if key not in data["additional_data_keys"]:
                data["additional_data_keys"].append(key)
        return data


class MonitoringSitesSchemaCruved(MonitoringCruvedSchemaMixin, MonitoringSitesSchema):
    pass


class MonitoringVisitsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringVisits
        load_instance = True
        load_relationships = True
        include_fk = True

    id_base_visit = auto_field(required=False, allow_none=True)
    pk = fields.Method("set_pk", dump_only=True)
    module = MA.Nested(ModuleSchema, data_key="module", dump_only=True)
    medias = MA.Nested(MediaSchema, many=True)
    visit_date_min = MA.Date()
    visit_date_max = MA.Date()

    observers = MA.Pluck(ObserverSchema, "id_role", many=True)

    parents = fields.Method("get_parents", dump_only=True)

    def get_parents(self, obj):
        parents = {}
        hierarchy_list = ["site", "site.sites_group"]
        parents = generate_parents_data(hierarchy_list, obj)
        return parents

    def set_pk(self, obj):
        return "id_base_visit"

    @pre_load
    def normalize(self, data, **kwargs):
        data["medias"] = data.get("medias") or []
        data["visit_date_max"] = data.get("visit_date_max") or data.get("visit_date_min")
        data["id_module"] = data.get("id_module") or g.current_module.id_module

        return data


class MonitoringVisitsSchemaCruved(MonitoringCruvedSchemaMixin, MonitoringVisitsSchema):
    pass


class MonitoringObservationsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringObservations
        load_instance = True
        load_relationships = True
        include_fk = True

    id_observation = auto_field(required=False, allow_none=True)
    medias = MA.Nested(MediaSchema, many=True)
    pk = fields.Method("set_pk", dump_only=True)
    id_base_site = fields.Method("set_id_base_site", dump_only=True)

    def set_pk(self, obj):
        return "id_observation"

    def set_id_base_site(self, obj):
        return obj.visit.id_base_site

    @pre_load
    def normalize(self, data, **kwargs):
        data["medias"] = data.get("medias") or []

        return data

    parents = fields.Method("get_parents", dump_only=True)

    def get_parents(self, obj):
        parents = {}
        hierarchy_list = ["visit", "visit.site", "visit.site.sites_group"]
        parents = generate_parents_data(hierarchy_list, obj)


class MonitoringObservationsSchemaCruved(
    MonitoringCruvedSchemaMixin, MonitoringObservationsSchema
):
    pass


class MonitoringObservationsDetailsSchema(MA.SQLAlchemyAutoSchema):
    class Meta:
        model = TMonitoringObservationDetails
        include_fk = True
        load_relationships = True
        load_instance = True

    id_observation_detail = auto_field(required=False, allow_none=True)
    pk = fields.Method("set_pk", dump_only=True)
    medias = MA.Nested(MediaSchema, many=True)
    id_base_site = fields.Method("set_id_base_site", dump_only=True)
    id_base_visit = fields.Method("set_id_base_visit", dump_only=True)

    parents = fields.Method("get_parents", dump_only=True)

    def get_parents(self, obj):
        parents = {}
        hierarchy_list = [
            "observation",
            "observation.visit",
            "observation.visit.site",
            "observation.visit.site.sites_group",
        ]
        parents = generate_parents_data(hierarchy_list, obj)

    def set_pk(self, obj):
        return "id_observation_detail"

    def set_id_base_site(self, obj):
        return obj.observation.visit.id_base_site

    def set_id_base_visit(self, obj):
        return obj.observation.visit.id_base_visit

    @pre_load
    def normalize(self, data, **kwargs):
        data["medias"] = data.get("medias") or []

        return data


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
