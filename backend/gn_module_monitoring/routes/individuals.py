from flask import g, request
from gn_module_monitoring.config.utils import get_module, get_specific_properties
from marshmallow import EXCLUDE
from sqlalchemy import select
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from geonature.utils.env import db

from geonature.core.gn_permissions import decorators as permissions
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
    process_json_data_for_db_upsert,
    sort,
    sort_according_to_column_type_for_site,
)

default_route_object_type = "individual"
OBJECT_CODE = "MONITORINGS_INDIVIDUALS"


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
    specific_properties = get_specific_properties(
        TMonitoringIndividuals, config, "individual"
    ).keys()

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
    "/individuals/<string:module_code>/<int:id>",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code=OBJECT_CODE)
def get_individual_by_id(scope: int, module_code: str, id: int, object_type: str):
    individual = db.get_or_404(TMonitoringIndividuals, id)
    if not individual.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot read individual {individual.id_individual}")
    data = MonitoringIndividualsSchema().dump(individual)

    return data


@blueprint.route(
    "/<string:module_code>/individuals",
    methods=["POST"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("C", object_code=OBJECT_CODE)
def post_individual(object_type: str, module_code: str):
    post_data = dict(request.get_json())
    return create_or_update_individual(post_data, module_code=module_code)


@blueprint.route(
    "/<string:module_code>/individuals/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code=OBJECT_CODE)
def patch_individual(scope, object_type: str, module_code: str, _id: int):
    individual = db.get_or_404(TMonitoringIndividuals, _id)
    if not individual.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot update individual {individual.id_individual}"
        )
    post_data = dict(request.get_json())
    print(post_data)
    if not "id_individual" in post_data:
        post_data["id_individual"] = _id
    return create_or_update_individual(post_data, module_code=module_code)


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


def create_or_update_individual(post_data: dict, module_code: str = "generic"):
    """
    Create or update an individual.

    :param post_data: dict containing data to create or update an individual
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized individual
    """
    config = get_config(module_code, force=True)
    process_data = process_json_data_for_db_upsert(config, post_data, default_route_object_type)
    try:
        individual = MonitoringIndividualsSchema(unknown=EXCLUDE).load(process_data)
    except Exception as e:
        raise Exception(f"create_or_update_individual : {str(e)}")
    db.session.add(individual)
    db.session.commit()

    return MonitoringIndividualsSchema().dump(individual)
