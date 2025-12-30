import json

from flask import jsonify, request, g

from marshmallow import EXCLUDE, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from geonature.utils.env import db
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.decorators import check_cruved_scope

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringSitesGroups,
    TMonitoringModules,
)
from gn_module_monitoring.monitoring.schemas import (
    MonitoringSitesGroupsSchema,
    MonitoringSitesGroupsSchemaCruved,
    add_specific_attributes,
)
from gn_module_monitoring.utils.errors.errorHandler import InvalidUsage
from gn_module_monitoring.utils.routes import (
    filter_params,
    geojson_query,
    get_limit_page,
    get_sort,
    paginate_scope,
    sort,
    process_json_data_for_db_upsert,
)
from gn_module_monitoring.routes.monitoring import (
    get_serialized_object,
)
from gn_module_monitoring.utils.utils import to_int


@blueprint.route("/sites_groups/config", methods=["GET"])
def get_config_sites_groups(id=None, module_code="generic", object_type="sites_group"):
    # A QUOI SERT CETTE ROUTE
    obj = get_serialized_object(module_code, object_type, id)
    return obj["properties"]


@blueprint.route("/sites_groups", methods=["GET"], defaults={"object_type": "sites_group"})
@blueprint.route(
    "/refacto/<string:module_code>/sites_groups",
    methods=["GET"],
    defaults={"object_type": "sites_group"},
)
@check_cruved_scope("R", object_code="MONITORINGS_GRP_SITES")
def get_sites_groups(object_type: str, module_code=None):
    object_code = "MONITORINGS_GRP_SITES"
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)

    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_sites_group", default_direction="desc"
    )
    query = select(TMonitoringSitesGroups)

    if module_code:
        query = query.where(
            TMonitoringSitesGroups.modules.any(TMonitoringModules.module_code == module_code)
        )

    query = filter_params(TMonitoringSitesGroups, query=query, params=params)

    # PATCH order by modules
    if sort_label == "modules":
        query = query.join(TMonitoringSitesGroups.modules)
        module_order = TMonitoringModules.module_label
        if sort_dir == "desc":
            module_order = module_order.desc()
        query = query.order_by(module_order)
    else:
        query = sort(TMonitoringSitesGroups, query=query, sort=sort_label, sort_dir=sort_dir)

    query_allowed = TMonitoringSitesGroups.filter_by_readable(
        query=query, object_code=object_code, module_code=g.current_module.module_code
    )

    config = get_config(module_code)
    query_allowed = TMonitoringSitesGroups.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=config.get("sites_group", {}).get("specific", {}),
    )

    if module_code:
        schema = add_specific_attributes(MonitoringSitesGroupsSchema, object_type, module_code)
    else:
        schema = MonitoringSitesGroupsSchema

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/sites_groups/<string:module_code>/<int:id_sites_group>",
    methods=["GET"],
    defaults={"object_type": "sites_group"},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code="MONITORINGS_GRP_SITES")
def get_sites_group_by_id(scope, module_code, id_sites_group: int, object_type: str):
    sites_group = db.get_or_404(TMonitoringSitesGroups, id_sites_group)
    if not sites_group.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot read site group {sites_group.id_sites_group}"
        )
    schema = MonitoringSitesGroupsSchemaCruved()

    return schema.dump(sites_group)


@blueprint.route(
    "/sites_groups/geometries", methods=["GET"], defaults={"object_type": "sites_group"}
)
@blueprint.route(
    "/refacto/<string:module_code>/sites_groups/geometries",
    methods=["GET"],
    defaults={"object_type": "site"},
)
@check_cruved_scope("R")
def get_sites_group_geometries(object_type: str, module_code=None):

    if g.current_module:
        module_code = g.current_module.module_code
    else:
        module_code = MODULE_CODE

    params = request.args.to_dict(flat=True)
    object_code = "MONITORINGS_GRP_SITES"
    query = select(TMonitoringSitesGroups)
    query = TMonitoringSitesGroups.filter_by_readable(
        query=query, module_code=module_code, object_code=object_code
    )
    query = TMonitoringSitesGroups.filter_by_params(query=query, params=params)

    if module_code != MODULE_CODE:
        query = query.where(
            TMonitoringSitesGroups.modules.any(TMonitoringModules.module_code == module_code)
        )

    alias_sites = aliased(TMonitoringSites)
    subquery_not_geom = (
        query.with_only_columns(
            TMonitoringSitesGroups.id_sites_group,
            TMonitoringSitesGroups.sites_group_name,
            func.st_convexHull(func.st_collect(alias_sites.geom)),
        )
        .group_by(TMonitoringSitesGroups.id_sites_group, TMonitoringSitesGroups.sites_group_name)
        .join(
            alias_sites,
            alias_sites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
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
    post_data = dict(request.get_json())
    sites_group = create_or_update_site_group(post_data, module_code)
    return sites_group


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
    post_data = dict(request.get_json())
    sites_group = create_or_update_site_group(post_data, module_code)
    return sites_group


@blueprint.errorhandler(ValidationError)
def handle_validation_error(error):
    return InvalidUsage(
        "Fields cannot be validated, message : {}".format(error.messages),
        status_code=422,
        payload=error.data,
    ).to_dict()


def create_or_update_site_group(post_data: dict, module_code: str = "generic"):
    """
    Create or update a site group.

    :param post_data: dict containing data to create or update a site group
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized site group
    """
    config = get_config(module_code)
    process_data = process_json_data_for_db_upsert(config, post_data, "sites_group")

    sites_group = MonitoringSitesGroupsSchema(unknown=EXCLUDE).load(process_data)
    db.session.add(sites_group)
    db.session.commit()
    return MonitoringSitesGroupsSchema().dump(sites_group)
