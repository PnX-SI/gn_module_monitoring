from flask import request, current_app, g
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.config.utils import get_specific_properties
from gn_module_monitoring.config.utils import get_specific_properties
from marshmallow import EXCLUDE
from werkzeug.exceptions import Forbidden
from gn_module_monitoring.command import permissions
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import MultiDict

from geonature.utils.env import db

from gn_module_monitoring.blueprint import blueprint
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.tools import get_scope
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
    get_objet_with_permission_boolean,
)
from gn_module_monitoring.routes.modules import get_modules

default_route_object_type = "observation_detail"
OBJECT_CODE = "MONITORINGS_VISITES"


@blueprint.route(
    "/refacto/obs_details/<int:_id>",
    methods=["DELETE"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("D", get_scope=True, object_code=OBJECT_CODE)
def delete_obs_detail(scope, _id, object_type):
    obs_detail = db.get_or_404(TMonitoringObservationDetails, _id)
    if not obs_detail.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot delete observation detail {obs_detail.id_base_obs_detail}"
        )
    db.session.delete(obs_detail)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route(
    "/<string:module_code>/obs_details",
    methods=["POST"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("C", object_code=OBJECT_CODE)
def post_obs_detail(object_type, module_code):
    post_data = dict(request.get_json())
    return create_or_update_obs_detail(post_data, module_code=module_code)


@blueprint.route(
    "/<string:module_code>/obs_details/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code=OBJECT_CODE)
def patch_obs_detail(scope, object_type: str, module_code: str, _id: int):
    obs_detail = db.get_or_404(TMonitoringObservationDetails, _id)
    if not obs_detail.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot update observation detail {obs_detail.id_base_obs_detail}"
        )
    post_data = dict(request.get_json())
    if not "id_observation_detail" in post_data:
        post_data["id_observation_detail"] = _id
    return create_or_update_obs_detail(post_data, module_code=module_code)


@blueprint.route(
    "/obs_details", methods=["GET"], defaults={"object_type": default_route_object_type}
)
@blueprint.route(
    "/refacto/<string:module_code>/obs_details",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
def get_obs_details(object_type, module_code=None):
    object_code = "MONITORINGS_VISITES"
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)

    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_observation_detail", default_direction="desc"
    )
    query = select(TMonitoringObservationDetails)

    if module_code:
        query = query.where(
            TMonitoringObservations.visit.has(
                TMonitoringVisits.module.has(TMonitoringModules.module_code == module_code)
            )
        )

    query = filter_params(TMonitoringObservationDetails, query=query, params=params)

    # PATCH order by modules
    if sort_label == "modules":
        query = (
            query.join(TMonitoringObservationDetails.observation)
            .join(TMonitoringObservations.visit)
            .join(TMonitoringVisits.module)
        )
        module_order = TMonitoringModules.module_label
        if sort_dir == "desc":
            module_order = module_order.desc()
        query = query.order_by(module_order)
    else:
        query = sort(
            TMonitoringObservationDetails, query=query, sort=sort_label, sort_dir=sort_dir
        )

    query_allowed = TMonitoringObservationDetails.filter_by_readable(
        query=query,
        object_code=object_code,
        module_code=module_code or g.current_module.module_code,
    )
    specific_properties = get_specific_properties(
        TMonitoringObservationDetails, get_config(module_code, force=True), "observation_detail"
    )
    query_allowed = TMonitoringObservationDetails.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=specific_properties,
    )
    print("query_allowed", query_allowed, "module_code", module_code)
    if module_code:
        schema = add_specific_attributes(
            MonitoringObservationsDetailsSchema, object_type, module_code
        )
    else:
        schema = MonitoringObservationsDetailsSchema

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/obs_details/<string:module_code>/<int:id>",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code=OBJECT_CODE)
def get_obs_detail_by_id(scope, module_code, id, object_type):
    # print(scope, module_code, id, object_type)
    obs_detail = db.get_or_404(TMonitoringObservationDetails, id)
    if not obs_detail.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot read observation detail {obs_detail.id_base_obs_detail}"
        )
    schema = add_specific_attributes(MonitoringObservationsDetailsSchema, object_type, module_code)

    data = schema().dump(obs_detail)

    return data


def create_or_update_obs_detail(post_data: dict, module_code: str = "generic"):
    """
    Create or update an observation detail.

    :param post_data: dict containing data to create or update an observation detail
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized observation detail
    """
    config = get_config(module_code, force=True)
    # print(config, "config", module_code, "module_code")
    process_data = process_json_data_for_db_upsert(config, post_data, default_route_object_type)

    obs_detail = MonitoringObservationsDetailsSchema(unknown=EXCLUDE).load(process_data)

    db.session.add(obs_detail)
    db.session.commit()

    schema = add_specific_attributes(
        MonitoringObservationsDetailsSchema, default_route_object_type, module_code
    )
    return schema().dump(obs_detail)
