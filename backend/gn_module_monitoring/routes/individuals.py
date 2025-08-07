from flask import g, request
from sqlalchemy import select
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from geonature.utils.env import db

from geonature.core.gn_permissions.decorators import check_cruved_scope
from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringIndividuals,
)
from gn_module_monitoring.monitoring.schemas import MonitoringIndividualsSchema
from gn_module_monitoring.routes.modules import get_modules

from gn_module_monitoring.utils.routes import (
    filter_params,
    get_limit_page,
    get_sort,
    paginate,
    paginate_scope,
    sort,
    sort_according_to_column_type_for_site,
)


@blueprint.route("/refacto/individuals", methods=["GET"], defaults={"object_type": "individual"})
@blueprint.route(
    "/refacto/<string:module_code>/individuals",
    methods=["GET"],
    defaults={"object_type": "individual"},
)
@check_cruved_scope("R", object_code="MONITORINGS_INDIVIDUALS")
def get_individuals(object_type, module_code=None):
    object_code = "MONITORINGS_INDIVIDUALS"
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_individual", default_direction="desc"
    )

    query = select(TMonitoringIndividuals)

    if module_code:
        query = query.where(
            TMonitoringIndividuals.modules.any(TMonitoringModules.module_code == module_code)
        )

    config = get_config(g.current_module.module_code)
    specific_properties = config.get("individuals", {}).get("specific", {})

    query = filter_params(TMonitoringIndividuals, query=query, params=params)
    query = sort(TMonitoringIndividuals, query, sort_label, sort_dir, specific_properties)

    query_allowed = TMonitoringIndividuals.filter_by_readable(
        query=query, module_code=g.current_module.module_code, object_code=object_code
    )

    schema = MonitoringIndividualsSchema

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


@blueprint.route(
    "/individuals/<int:_id>", methods=["DELETE"], defaults={"object_type": "individual"}
)
@check_cruved_scope("D", get_scope=True, object_code="MONITORINGS_INDIVIDUALS")
def delete_individual(scope, _id: int, object_type: str):
    individual = db.get_or_404(TMonitoringIndividuals, _id)
    if not individual.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot delete site group {individual.id_individual}"
        )
    db.session.delete(individual)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200
