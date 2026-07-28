from flask import request, current_app, g
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.repositories import get_config
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
from gn_module_monitoring.monitoring.models import TMonitoringVisits, TMonitoringModules
from gn_module_monitoring.monitoring.schemas import (
    MonitoringVisitsSchemaCruved,
    MonitoringVisitsSchema,
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

default_route_object_type = "visit"


@blueprint.route(
    "/refacto/visits/<int:_id>",
    methods=["DELETE"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("D", get_scope=True, object_code="MONITORINGS_VISITES")
def delete_visit(scope, _id, object_type):
    visit = db.get_or_404(TMonitoringVisits, _id)
    if not visit.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot delete visit {visit.id_base_visit}")
    db.session.delete(visit)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route(
    "/<string:module_code>/visits",
    methods=["POST"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("C", object_code="MONITORINGS_VISITES")
def post_visit(object_type, module_code):
    post_data = dict(request.get_json())
    return create_or_update_visit(post_data, module_code=module_code)


@blueprint.route(
    "/<string:module_code>/visits/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code="MONITORINGS_VISITES")
def patch_visit(scope, object_type: str, module_code: str, _id: int):
    visit = db.get_or_404(TMonitoringVisits, _id)
    if not visit.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot update visit {visit.id_base_visit}")
    post_data = dict(request.get_json())
    if not "id_base_visit" in post_data:
        post_data["id_base_visit"] = _id
    return create_or_update_visit(post_data, module_code=module_code)


@blueprint.route("/visits", methods=["GET"], defaults={"object_type": default_route_object_type})
@blueprint.route(
    "/refacto/<string:module_code>/visits",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
def get_visits(object_type, module_code=None):
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_base_visit", default_direction="desc"
    )
    modules_object = get_modules()

    # FIXME: check permission according to module in param if any
    # Retrieves visits that do not depend on modules
    OBJECT_CODE = "MONITORINGS_VISITES"

    modules = get_objet_with_permission_boolean(modules_object, object_code=OBJECT_CODE)
    ids_modules_allowed = [module["id_module"] for module in modules if module["cruved"]["R"]]

    query = select(TMonitoringVisits)
    query = query.options(joinedload(TMonitoringVisits.module)).where(
        TMonitoringVisits.id_module.in_(ids_modules_allowed)
    )
    query = filter_params(TMonitoringVisits, query=query, params=params)
    query = sort(model=TMonitoringVisits, query=query, sort=sort_label, sort_dir=sort_dir)
    if module_code:
        query = query.where(
            TMonitoringVisits.module.has(TMonitoringModules.module_code == module_code)
        )
    query_allowed = query
    for module in modules:
        if module["id_module"] in ids_modules_allowed:
            query_allowed = TMonitoringVisits.filter_by_readable(
                query=query_allowed, module_code=module["module_code"], object_code=OBJECT_CODE
            )
    return paginate_scope(
        query=query_allowed,
        schema=MonitoringVisitsSchema,
        limit=limit,
        page=page,
        object_code=OBJECT_CODE,
        schema_extra_args={
            "exclude": (
                "items.parents",
                "items.medias",
            )
        },
    )


@blueprint.route(
    "/visits/<string:module_code>/<int:id>",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code="MONITORINGS_VISITES")
def get_visit_by_id(scope, module_code, id, object_type):
    # print(scope, module_code, id, object_type)
    visit = db.get_or_404(TMonitoringVisits, id)
    if not visit.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot read visit {visit.id_base_visit}")
    schema = add_specific_attributes(MonitoringVisitsSchema, object_type, module_code)

    data = schema(exclude=("module",)).dump(visit)

    return data


def create_or_update_visit(post_data: dict, module_code: str = "generic"):
    """
    Create or update a visit.

    :param post_data: dict containing data to create or update a visit
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized visit
    """
    config = get_config(module_code, force=True)
    # print(config, "config", module_code, "module_code")
    process_data = process_json_data_for_db_upsert(config, post_data, default_route_object_type)

    try:
        visit = MonitoringVisitsSchema(unknown=EXCLUDE).load(process_data)
    except Exception as e:
        print(e.__dict__)
        raise e
    db.session.add(visit)
    db.session.commit()

    schema = add_specific_attributes(
        MonitoringVisitsSchema, default_route_object_type, module_code
    )
    return schema().dump(visit)
