from flask import request, current_app, g
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.config.utils import get_specific_properties
from gn_module_monitoring.config.utils import get_specific_properties
from marshmallow import EXCLUDE
from werkzeug.exceptions import Forbidden
from gn_module_monitoring.command import permissions
from sqlalchemy import select
from werkzeug.datastructures import MultiDict

from geonature.utils.env import db

from gn_module_monitoring.constants import ObjectType
from gn_module_monitoring.utils.utils import get_permission_object_code
from gn_module_monitoring.blueprint import blueprint, ROUTE_PREFIX
from geonature.core.gn_permissions import decorators as permissions
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringObservationDetails,
    TMonitoringObservations,
    TMonitoringVisits,
)
from gn_module_monitoring.monitoring.schemas import (
    MonitoringObservationsDetailsSchema,
    add_specific_attributes,
)
from gn_module_monitoring.utils.routes import (
    filter_params,
    get_limit_page,
    get_sort,
    paginate_scope,
    process_json_data_for_db_upsert,
    sort,
)

OBJECT_CODE = get_permission_object_code(ObjectType.OBSERVATION_DETAIL)


@blueprint.route(
    f"{ROUTE_PREFIX}/<string:module_code>/observation_details/<int:_id>", methods=["DELETE"]
)
@permissions.check_cruved_scope("D", get_scope=True, object_code=OBJECT_CODE)
def delete_obs_detail(scope, _id: int, module_code: str):
    obs_detail = db.get_or_404(TMonitoringObservationDetails, _id)
    if not obs_detail.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot delete observation detail {obs_detail.id_base_obs_detail}"
        )
    db.session.delete(obs_detail)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route(f"{ROUTE_PREFIX}/<string:module_code>/observation_details", methods=["POST"])
@permissions.check_cruved_scope("C", object_code=OBJECT_CODE)
def post_obs_detail(module_code: str):
    post_data = dict(request.get_json())
    return create_or_update_obs_detail(post_data, module_code=module_code)


@blueprint.route(
    f"{ROUTE_PREFIX}/<string:module_code>/observation_details/<int:_id>", methods=["PATCH"]
)
@permissions.check_cruved_scope("U", get_scope=True, object_code=OBJECT_CODE)
def patch_obs_detail(scope, module_code: str, _id: int):
    obs_detail = db.get_or_404(TMonitoringObservationDetails, _id)
    if not obs_detail.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot update observation detail {obs_detail.id_base_obs_detail}"
        )
    post_data = dict(request.get_json())
    if not "id_observation_detail" in post_data:
        post_data["id_observation_detail"] = _id
    return create_or_update_obs_detail(post_data, module_code=module_code)


@blueprint.route(f"{ROUTE_PREFIX}/<string:module_code>/observation_details", methods=["GET"])
def get_obs_details(module_code: str):
    object_code = get_permission_object_code(ObjectType.OBSERVATION_DETAIL)
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)

    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_observation_detail", default_direction="desc"
    )
    query = select(TMonitoringObservationDetails)

    query = query.where(
        TMonitoringObservations.visit.has(
            TMonitoringVisits.module.has(TMonitoringModules.module_code == module_code)
        )
    )

    query = filter_params(TMonitoringObservationDetails, query=query, params=params)

    query = sort(TMonitoringObservationDetails, query=query, sort=sort_label, sort_dir=sort_dir)

    query_allowed = TMonitoringObservationDetails.filter_by_readable(
        query=query,
        object_code=object_code,
        module_code=module_code or g.current_module.module_code,
    )
    specific_properties = get_specific_properties(
        TMonitoringObservationDetails, get_config(module_code), ObjectType.OBSERVATION_DETAIL
    )
    query_allowed = TMonitoringObservationDetails.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=specific_properties,
    )
    schema = add_specific_attributes(
        MonitoringObservationsDetailsSchema, ObjectType.OBSERVATION_DETAIL, module_code
    )

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
        schema_extra_args={
            "exclude": (
                "items.parents",
                "items.medias",
            )
        },
    )


@blueprint.route(
    f"{ROUTE_PREFIX}/<string:module_code>/observation_details/<int:id>", methods=["GET"]
)
@permissions.check_cruved_scope("R", get_scope=True, object_code=OBJECT_CODE)
def get_obs_detail_by_id(scope: int, module_code: str, id: int):
    obs_detail = db.get_or_404(TMonitoringObservationDetails, id)
    if not obs_detail.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot read observation detail {obs_detail.id_base_obs_detail}"
        )
    schema = add_specific_attributes(
        MonitoringObservationsDetailsSchema, ObjectType.OBSERVATION_DETAIL, module_code
    )

    data = schema().dump(obs_detail)

    return data


def create_or_update_obs_detail(post_data: dict, module_code: str = "generic"):
    """
    Create or update an observation detail.

    :param post_data: dict containing data to create or update an observation detail
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized observation detail
    """
    config = get_config(module_code)
    process_data = process_json_data_for_db_upsert(
        config, post_data, ObjectType.OBSERVATION_DETAIL
    )

    obs_detail = MonitoringObservationsDetailsSchema(unknown=EXCLUDE).load(process_data)

    db.session.add(obs_detail)
    db.session.commit()

    schema = add_specific_attributes(
        MonitoringObservationsDetailsSchema, ObjectType.OBSERVATION_DETAIL, module_code
    )
    return schema().dump(obs_detail)
