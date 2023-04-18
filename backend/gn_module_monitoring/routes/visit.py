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
    sort,
)

# Retrieves visits that do not depend on modules


@blueprint.route("/visits", methods=["GET"])
def get_visits():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_base_visit", default_direction="desc"
    )
    query = TMonitoringVisits.query.options(joinedload(TMonitoringVisits.module))
    query = filter_params(query=query, params=params)
    query = sort(query=query, sort=sort_label, sort_dir=sort_dir)

    return paginate(
        query=query,
        schema=MonitoringVisitsSchema,
        limit=limit,
        page=page,
    )
