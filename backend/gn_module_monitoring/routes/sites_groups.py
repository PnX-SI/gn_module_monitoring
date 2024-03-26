import json

from flask import jsonify, request, g

from marshmallow import ValidationError
from sqlalchemy import func, select
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from geonature.utils.env import db
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.decorators import check_cruved_scope

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import TMonitoringSites, TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema
from gn_module_monitoring.utils.errors.errorHandler import InvalidUsage
from gn_module_monitoring.utils.routes import (
    filter_params,
    geojson_query,
    get_limit_page,
    get_sort,
    paginate_scope,
    sort,
    get_objet_with_permission_boolean,
)
from gn_module_monitoring.routes.monitoring import (
    create_or_update_object_api,
    get_config_object,
)
from gn_module_monitoring.utils.utils import to_int


@blueprint.route("/sites_groups/config", methods=["GET"])
def get_config_sites_groups(id=None, module_code="generic", object_type="sites_group"):
    obj = get_config_object(module_code, object_type, id)
    return obj["properties"]


@blueprint.route("/sites_groups", methods=["GET"], defaults={"object_type": "sites_group"})
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES")
def get_sites_groups(object_type: str):
    object_code = "MONITORINGS_GRP_SITES"
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)

    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_sites_group", default_direction="desc"
    )
    query = select(TMonitoringSitesGroups)
    query = filter_params(TMonitoringSitesGroups, query=query, params=params)

    query = sort(TMonitoringSitesGroups, query=query, sort=sort_label, sort_dir=sort_dir)

    query_allowed = TMonitoringSitesGroups.filter_by_readable(query=query, object_code=object_code)
    return paginate_scope(
        query=query_allowed,
        schema=MonitoringSitesGroupsSchema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/sites_groups/<int:id_sites_group>", methods=["GET"], defaults={"object_type": "sites_group"}
)
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES")
@permissions.check_cruved_scope(
    "R", get_scope=True, module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES"
)
def get_sites_group_by_id(scope, id_sites_group: int, object_type: str):
    sites_group = db.get_or_404(TMonitoringSitesGroups, id_sites_group)
    if not sites_group.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot read site group {sites_group.id_sites_group}"
        )
    schema = MonitoringSitesGroupsSchema()
    response = schema.dump(sites_group)
    response["cruved"] = get_objet_with_permission_boolean(
        [sites_group], object_code="MONITORINGS_GRP_SITES"
    )[0]["cruved"]
    response["geometry"] = (
        json.loads(response["geometry"])
        if response["geometry"] != None and isinstance(response["geometry"], str)
        else response["geometry"]
    )
    return response


@blueprint.route(
    "/sites_groups/geometries", methods=["GET"], defaults={"object_type": "sites_group"}
)
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES")
def get_sites_group_geometries(object_type: str):

    params = request.args.to_dict(flat=True)
    object_code = "MONITORINGS_GRP_SITES"
    query = select(TMonitoringSitesGroups)
    query = TMonitoringSitesGroups.filter_by_readable(query=query, object_code=object_code)
    query = TMonitoringSitesGroups.filter_by_params(query=query, params=params)
    subquery_not_geom = (
        query.with_only_columns(
            TMonitoringSitesGroups.id_sites_group,
            TMonitoringSitesGroups.sites_group_name,
            func.st_convexHull(func.st_collect(TMonitoringSites.geom)),
        )
        .group_by(TMonitoringSitesGroups.id_sites_group, TMonitoringSitesGroups.sites_group_name)
        .join(
            TMonitoringSites,
            TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
        )
        .where(TMonitoringSitesGroups.geom == None)
    )

    subquery_with_geom = (
        query.with_only_columns(
            TMonitoringSitesGroups.id_sites_group,
            TMonitoringSitesGroups.sites_group_name,
            TMonitoringSitesGroups.geom,
        ).where(TMonitoringSitesGroups.geom != None)
    ).distinct()

    results = geojson_query(subquery_not_geom.union(subquery_with_geom).alias("grp_site"))

    return jsonify(results)


@blueprint.route(
    "/sites_groups/<int:_id>", methods=["PATCH"], defaults={"object_type": "sites_group"}
)
@permissions.check_cruved_scope(
    "U", get_scope=True, module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES"
)
def patch(scope, _id: int, object_type: str):
    # ###############################""
    # FROM route/monitorings
    sites_group = db.get_or_404(TMonitoringSitesGroups, _id)
    if not sites_group.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot update site group {sites_group.id_sites_group}"
        )

    module_code = "generic"
    get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type, _id), 201


@blueprint.route(
    "/sites_groups/<int:_id>", methods=["DELETE"], defaults={"object_type": "sites_group"}
)
@permissions.check_cruved_scope(
    "D", get_scope=True, module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES"
)
def delete(scope, _id: int, object_type: str):
    sites_group = db.get_or_404(TMonitoringSitesGroups, _id)
    if not sites_group.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot delete site group {sites_group.id_sites_group}"
        )
    db.session.delete(sites_group)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route("/sites_groups", methods=["POST"], defaults={"object_type": "sites_group"})
@check_cruved_scope("C", module_code=MODULE_CODE, object_code="MONITORINGS_GRP_SITES")
def post(object_type: str):
    module_code = "generic"
    get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type), 201


@blueprint.errorhandler(ValidationError)
def handle_validation_error(error):
    return InvalidUsage(
        "Fields cannot be validated, message : {}".format(error.messages),
        status_code=422,
        payload=error.data,
    ).to_dict()
