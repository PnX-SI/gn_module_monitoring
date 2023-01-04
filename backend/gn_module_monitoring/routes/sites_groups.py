from flask import request
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.utils.routes import (
    filter_params,
    get_limit_offset,
    get_sort,
    paginate,
    sort,
)
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema


@blueprint.route("/sites_groups", methods=["GET"])
def get_sites_groups():
    params = MultiDict(request.args)
    limit, page = get_limit_offset(params=params)
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
