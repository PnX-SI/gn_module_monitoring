from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.blueprint import blueprint
from geonature.core.gn_permissions.decorators import check_cruved_scope
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
)
from sqlalchemy import select
from gn_module_monitoring.utils.routes import sort
from werkzeug.datastructures import MultiDict

from geonature.core.gn_permissions import decorators as permissions

from flask import request, g


@blueprint.route("/observations", methods=["GET"], defaults={"object_type": "observation"})
@blueprint.route(
    "/refacto/<string:module_code>/observations",
    methods=["GET"],
    defaults={"object_type": "observation"},
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

    # PATCH order by modules
    if sort_label == "modules":
        query = query.join(TMonitoringObservations.visits).join(TMonitoringVisits.module)
        module_order = TMonitoringModules.module_label
        if sort_dir == "desc":
            module_order = module_order.desc()
        query = query.order_by(module_order)
    else:
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
    if module_code:
        schema = add_specific_attributes(MonitoringObservationsSchema, object_type, module_code)
    else:
        schema = MonitoringObservationsSchema

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/observation/geometries", methods=["GET"], defaults={"object_type": "observation"}
)
@blueprint.route(
    "/refacto/<string:module_code>/observation/geometries",
    methods=["GET"],
    defaults={"object_type": "observation"},
)
@permissions.check_cruved_scope("R")
def obs_geometries(object_type: str, module_code=None):
    return {}
