from flask import request, current_app, g
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.command.utils import get_module
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.config.utils import get_specific_properties
from marshmallow import EXCLUDE
from werkzeug.exceptions import Forbidden, NotFound
from sqlalchemy import select
from werkzeug.datastructures import MultiDict

from geonature.utils.env import db

from gn_module_monitoring.blueprint import blueprint
from geonature.core.gn_permissions import decorators as permissions
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringMarkingEvent,
)
from gn_module_monitoring.monitoring.schemas import (
    MonitoringMarkingSchema,
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

default_route_object_type = "marking"
OBJECT_CODE = "MONITORINGS_MARKINGS"


def get_marking_or_404(id_marking: int, id_module: int) -> TMonitoringMarkingEvent:
    # `id_marking` est utilisé directement plutôt que `db.get_or_404` car la clé primaire
    # de TMarkingEvent est composite (id_marking, id_module) : `id_marking` reste néanmoins
    # unique et suffisant pour identifier une ligne.
    marking = (
        db.session.execute(
            select(TMonitoringMarkingEvent).where(
                TMonitoringMarkingEvent.id_marking == id_marking,
                TMonitoringMarkingEvent.id_module == id_module,
            )
        )
        .unique()
        .scalar_one_or_none()
    )
    if marking is None:
        raise NotFound(f"Marking {id_marking} not found")
    return marking


@blueprint.route(
    "/refacto/markings/<int:_id>",
    methods=["DELETE"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("D", get_scope=True, object_code=OBJECT_CODE)
def delete_marking(scope, _id: int, object_type: str):
    marking = get_marking_or_404(_id, id_module=g.get("current_module").id_module)
    if not marking.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot delete marking {marking.id_marking}")
    db.session.delete(marking)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route(
    "/<string:module_code>/markings",
    methods=["POST"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("C", object_code=OBJECT_CODE)
def post_marking(object_type: str, module_code: str):
    post_data = dict(request.get_json())
    if not "id_module" in post_data:
        post_data["id_module"] = g.get("current_module").id_module
    return create_or_update_marking(post_data, module_code=module_code)


@blueprint.route(
    "/<string:module_code>/markings/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code=OBJECT_CODE)
def patch_marking(scope, object_type: str, module_code: str, _id: int):
    marking = get_marking_or_404(_id, id_module=g.get("current_module").id_module)
    if not marking.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot update marking {marking.id_marking}")
    post_data = dict(request.get_json())
    if not "id_marking" in post_data:
        post_data["id_marking"] = _id
    if not "id_module" in post_data:
        post_data["id_module"] = g.get("current_module").id_module
    return create_or_update_marking(post_data, module_code=module_code)


@blueprint.route(
    "/refacto/<string:module_code>/markings",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
def get_markings(object_type: str, module_code: str):
    object_code = OBJECT_CODE
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)

    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_marking", default_direction="desc"
    )
    query = select(TMonitoringMarkingEvent)

    query = query.join(
        TMonitoringModules, TMonitoringModules.id_module == TMonitoringMarkingEvent.id_module
    ).where(TMonitoringModules.module_code == module_code)

    query = filter_params(TMonitoringMarkingEvent, query=query, params=params)

    query = sort(TMonitoringMarkingEvent, query=query, sort=sort_label, sort_dir=sort_dir)

    query_allowed = TMonitoringMarkingEvent.filter_by_readable(
        query=query,
        object_code=object_code,
        module_code=module_code or g.current_module.module_code,
    )
    specific_properties = get_specific_properties(
        TMonitoringMarkingEvent, get_config(module_code, force=True), "marking"
    )
    query_allowed = TMonitoringMarkingEvent.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=specific_properties,
    )
    schema = add_specific_attributes(MonitoringMarkingSchema, object_type, module_code)

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/markings/<string:module_code>/<int:id>",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code=OBJECT_CODE)
def get_marking_by_id(scope: int, module_code: str, id: int, object_type: str):
    marking = get_marking_or_404(id, id_module=g.current_module.id_module)
    if not marking.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot read marking {marking.id_marking}")
    schema = add_specific_attributes(MonitoringMarkingSchema, object_type, module_code)

    data = schema().dump(marking)

    return data


def create_or_update_marking(post_data: dict, module_code: str = "generic"):
    """
    Create or update a marking.

    :param post_data: dict containing data to create or update a marking
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized marking
    """
    config = get_config(module_code, force=True)
    process_data = process_json_data_for_db_upsert(config, post_data, default_route_object_type)
    try:
        marking = MonitoringMarkingSchema(unknown=EXCLUDE).load(process_data)
    except Exception as e:
        print(f"Error loading marking data: {e}")
        raise

    db.session.add(marking)
    db.session.commit()

    schema = add_specific_attributes(
        MonitoringMarkingSchema, default_route_object_type, module_code
    )
    return schema().dump(marking)
