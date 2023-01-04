from flask import request
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema
from gn_module_monitoring.utils.routes import filter_params, get_limit_offset, paginate


@blueprint.route("/sites_groups", methods=["GET"])
def get_sites_groups():
    params = MultiDict(request.args)
    limit, page = get_limit_offset(params=params)

    query = filter_params(query=TMonitoringSitesGroups.query, params=params)

    query = query.order_by(TMonitoringSitesGroups.id_sites_group)
    return paginate(
        query=query,
        schema=MonitoringSitesGroupsSchema,
        limit=limit,
        page=page,
    )
