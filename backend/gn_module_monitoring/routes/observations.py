from marshmallow import EXCLUDE
from geonature.utils.env import db
from geonature.core.gn_permissions.decorators import check_cruved_scope
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.blueprint import blueprint

from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.config.utils import get_specific_properties
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringObservations,
    TMonitoringVisits,
)

from gn_module_monitoring.monitoring.schemas import (
    MonitoringObservationsSchema,
    add_specific_attributes,
)
from gn_module_monitoring.utils.routes import (
    filter_params,
    get_limit_page,
    get_sort,
    paginate_scope,
    process_json_data_for_db_upsert,
)
from sqlalchemy import select
from gn_module_monitoring.utils.routes import sort
from werkzeug.datastructures import MultiDict

from geonature.core.gn_permissions import decorators as permissions

from flask import request, g

default_route_object_type = "observation"


@blueprint.route(
    "/refacto/<string:module_code>/observations",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", object_code="MONITORINGS_VISITES")
def get_observations(object_type: str, module_code: str = None):
    object_code = "MONITORINGS_VISITES"
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)

    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_observation", default_direction="desc"
    )
    query = select(TMonitoringObservations)

    if module_code:
        query = query.where(
            TMonitoringObservations.visit.has(
                TMonitoringVisits.module.has(TMonitoringModules.module_code == module_code)
            )
        )

    query = filter_params(TMonitoringObservations, query=query, params=params)

    query = sort(TMonitoringObservations, query=query, sort=sort_label, sort_dir=sort_dir)

    query_allowed = TMonitoringObservations.filter_by_readable(
        query=query,
        object_code=object_code,
        module_code=module_code or g.current_module.module_code,
    )
    specific_properties = get_specific_properties(
        TMonitoringObservations, get_config(module_code, force=True), "observation"
    )
    query_allowed = TMonitoringObservations.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=specific_properties,
    )

    schema = MonitoringObservationsSchema

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/observation/geometries", methods=["GET"], defaults={"object_type": default_route_object_type}
)
@blueprint.route(
    "/refacto/<string:module_code>/observation/geometries",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R")
def obs_geometries(object_type: str, module_code=None):
    return {}


@blueprint.route(
    "/observations/<string:module_code>/<int:_id>",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code="MONITORINGS_VISITES")
def get_observation_by_id(scope, module_code, _id, object_type):
    observation = db.get_or_404(TMonitoringObservations, _id)
    if not observation.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot read observation {observation.id_observation}"
        )
    schema = add_specific_attributes(MonitoringObservationsSchema, object_type, module_code)

    data = schema().dump(observation)

    return data


@blueprint.route(
    "/<string:module_code>/observations/<int:_id>",
    methods=["DELETE"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("D", get_scope=True, object_code="MONITORINGS_VISITES")
def delete_observation(scope, _id, module_code, object_type):
    observation = db.get_or_404(TMonitoringObservations, _id)
    if not observation.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot delete observation {observation.id_observation}"
        )
    db.session.delete(observation)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route(
    "/<string:module_code>/observations",
    methods=["POST"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("C", object_code="MONITORINGS_VISITES")
def post_observation(object_type, module_code):
    post_data = dict(request.get_json())
    return create_or_update_observation(post_data, module_code=module_code)


@blueprint.route(
    "/<string:module_code>/observations/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code="MONITORINGS_VISITES")
def patch_observation(scope, object_type: str, module_code: str, _id: int):
    observation = db.get_or_404(TMonitoringObservations, _id)
    if not observation.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot update observation {observation.id_observation}"
        )
    post_data = dict(request.get_json())
    if not "id_observation" in post_data:
        post_data["id_observation"] = _id
    return create_or_update_observation(post_data, module_code=module_code)


def create_or_update_observation(post_data: dict, module_code: str = "generic"):
    """
    Create or update a observation.

    :param post_data: dict containing data to create or update a observation
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized observation
    """
    config = get_config(module_code, force=True)
    process_data = process_json_data_for_db_upsert(config, post_data, default_route_object_type)

    observation = MonitoringObservationsSchema(unknown=EXCLUDE).load(process_data)

    db.session.add(observation)
    db.session.commit()

    schema = add_specific_attributes(
        MonitoringObservationsSchema, default_route_object_type, module_code
    )
    return schema().dump(observation)
