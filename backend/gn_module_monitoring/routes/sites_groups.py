from flask import jsonify, request
from geonature.utils.env import db
from marshmallow import ValidationError
from sqlalchemy import func
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.modules.repositories import get_module
from gn_module_monitoring.monitoring.definitions import monitoring_definitions
from gn_module_monitoring.monitoring.models import TMonitoringSites, TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema
from gn_module_monitoring.utils.errors.errorHandler import InvalidUsage
from gn_module_monitoring.utils.routes import (
    filter_params,
    geojson_query,
    get_limit_page,
    get_sort,
    paginate,
    sort,
)
from gn_module_monitoring.routes.monitoring import create_or_update_object_api_sites_sites_group
from gn_module_monitoring.utils.utils import to_int


@blueprint.route("/sites_groups", methods=["GET"])
def get_sites_groups():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_sites_group", default_direction="desc"
    )
    query = filter_params(query=TMonitoringSitesGroups.query, params=params)

    query = sort(query=query, sort=sort_label, sort_dir=sort_dir)
    return paginate(
        query=query,
        schema=MonitoringSitesGroupsSchema,
        limit=limit,
        page=page,
    )


@blueprint.route("/sites_groups/<int:id_sites_group>", methods=["GET"])
def get_sites_group_by_id(id_sites_group: int):
    schema = MonitoringSitesGroupsSchema()
    result = TMonitoringSitesGroups.find_by_id(id_sites_group)
    return jsonify(schema.dump(result))


@blueprint.route("/sites_groups/geometries", methods=["GET"])
def get_sites_group_geometries():
    subquery = (
        db.session.query(
            TMonitoringSitesGroups.id_sites_group,
            TMonitoringSitesGroups.sites_group_name,
            func.st_convexHull(func.st_collect(TMonitoringSites.geom)),
        )
        .group_by(TMonitoringSitesGroups.id_sites_group, TMonitoringSitesGroups.sites_group_name)
        .join(
            TMonitoringSites,
            TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
        )
        .subquery()
    )

    result = geojson_query(subquery)

    return jsonify(result)


@blueprint.route("/sites_groups/<int:_id>", methods=["PATCH"])
def patch(_id):
    # ###############################""
    # FROM route/monitorings
    module_code = "generic"
    object_type = "sites_group"
    get_config(module_code, force=True)
    return create_or_update_object_api_sites_sites_group(module_code, object_type, _id), 201


@blueprint.route("/sites_groups/<int:_id>", methods=["DELETE"])
def delete(_id):
    item_schema = MonitoringSitesGroupsSchema()
    item = TMonitoringSitesGroups.find_by_id(_id)
    TMonitoringSitesGroups.query.filter_by(id_g=_id).delete()
    db.session.commit()
    return item_schema.dump(item), 201


@blueprint.route("/sites_groups", methods=["POST"])
def post():
    module_code = "generic"
    object_type = "sites_group"
    get_config(module_code, force=True)
    return create_or_update_object_api_sites_sites_group(module_code, object_type), 201


@blueprint.errorhandler(ValidationError)
def handle_validation_error(error):
    return InvalidUsage(
        "Fields cannot be validated, message : {}".format(error.messages),
        status_code=422,
        payload=error.data,
    ).to_dict()
