from flask import request
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.monitoring.models import TMonitoringVisits
from gn_module_monitoring.monitoring.schemas import MonitoringVisitsSchema
from gn_module_monitoring.utils.routes import (
    filter_params,
    get_limit_page,
    get_sort,
    paginate,
    paginate_scope,
    sort,
    get_objet_with_permission_boolean,
)
from gn_module_monitoring.routes.modules import get_modules
from gn_module_monitoring.monitoring.definitions import MonitoringPermissions_dict

# Retrieves visits that do not depend on modules
OBJECT_CODE = MonitoringPermissions_dict["visit"]


@blueprint.route("/visits", methods=["GET"], defaults={"object_type": "visit"})
def get_visits(object_type):
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_base_visit", default_direction="desc"
    )
    modules_object = get_modules()
    modules = get_objet_with_permission_boolean(modules_object, object_code=OBJECT_CODE)
    ids_modules_allowed = [module["id_module"] for module in modules if module["cruved"]["R"]]
    query = TMonitoringVisits.query
    query = query.options(joinedload(TMonitoringVisits.module)).filter(
        TMonitoringVisits.id_module.in_(ids_modules_allowed)
    )
    query = filter_params(query=query, params=params)
    query = sort(query=query, sort=sort_label, sort_dir=sort_dir)
    query_allowed = query
    for module in modules:
        if module["id_module"] in ids_modules_allowed:
            query_allowed = query_allowed.filter_by_readable(
                module_code=module["module_code"], object_code=OBJECT_CODE
            )
    return paginate_scope(
        query=query_allowed,
        schema=MonitoringVisitsSchema,
        limit=limit,
        page=page,
        object_code=OBJECT_CODE,
    )
