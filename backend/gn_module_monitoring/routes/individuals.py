from flask import g, request
from gn_module_monitoring.config.utils import get_specific_properties
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
OBJECT_CODE = "INDIVIDUALS"


@blueprint.route("/refacto/individuals", methods=["GET"], defaults={"object_type": "individual"})
@blueprint.route(
    "/refacto/<string:module_code>/individuals",
    methods=["GET"],
    defaults={"object_type": "individual"},
)
@check_cruved_scope("R", object_code=OBJECT_CODE)
def get_individuals(object_type, module_code=None):
    """
    List the individuals readable by the current user.

    Query string parameters handle pagination (`limit`, `page`), sorting
    (`sort`, `sort_dir`, default by `id_individual` descending), and filtering
    on individual columns.

    Parameters
    ----------
    object_type : str
        Object type, by default "individual".
    module_code : str, optional
        If given, only individuals associated with this module are returned.

    Returns
    -------
    flask.Response
        JSON response with the paginated serialized individuals (`items`,
        `count`, `limit`, `page`), each item including its `cruved` permissions.
    """
    object_code = OBJECT_CODE
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
        schema_extra_args={"exclude": ("items.medias",)},
    )


@blueprint.route(
    "/individuals/<string:module_code>/<int:id>",
    methods=["GET"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("R", get_scope=True, object_code=OBJECT_CODE)
def get_individual_by_id(scope: int, module_code: str, id: int, object_type: str):
    """
    Retrieve a single individual.

    Parameters
    ----------
    scope : int
        User scope for the "R" (read) action.
    module_code : str
        Code of the current module.
    id : int
        Identifier of the individual.
    object_type : str
        Object type, by default "individual".

    Returns
    -------
    dict
        Serialized individual.

    Raises
    ------
    NotFound
        If the individual does not exist.
    Forbidden
        If the user is not allowed to read the individual.
    """
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
    """
    Create an individual from the request JSON body.

    Parameters
    ----------
    object_type : str
        Object type, by default "individual".
    module_code : str
        Code of the module the individual is associated with.

    Returns
    -------
    dict
        Serialized created individual.
    """
    post_data = dict(request.get_json())
    return create_or_update_individual(post_data, module_code=module_code)


@blueprint.route(
    "/<string:module_code>/individuals/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": default_route_object_type},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code=OBJECT_CODE)
def patch_individual(scope, object_type: str, module_code: str, _id: int):
    """
    Update an individual from the request JSON body.

    If `id_individual` is missing from the body, it is filled with `_id`.

    Parameters
    ----------
    scope : int
        User scope for the "U" (update) action.
    object_type : str
        Object type, by default "individual".
    module_code : str
        Code of the module the individual is associated with.
    _id : int
        Identifier of the individual to update.

    Returns
    -------
    dict
        Serialized updated individual.

    Raises
    ------
    NotFound
        If the individual does not exist.
    Forbidden
        If the user is not allowed to update the individual.
    """
    individual = db.get_or_404(TMonitoringIndividuals, _id)
    if not individual.has_instance_permission(scope=scope):
        raise Forbidden(
            f"User {g.current_user} cannot update individual {individual.id_individual}"
        )
    post_data = dict(request.get_json())
    if not "id_individual" in post_data:
        post_data["id_individual"] = _id
    return create_or_update_individual(post_data, module_code=module_code)


@blueprint.route(
    "/individuals/<int:_id>", methods=["DELETE"], defaults={"object_type": "individual"}
)
@check_cruved_scope("D", get_scope=True, object_code=OBJECT_CODE)
def delete_individual(scope, _id: int, object_type: str):
    """
    Delete an individual.

    Parameters
    ----------
    scope : int
        User scope for the "D" (delete) action.
    _id : int
        Identifier of the individual to delete.
    object_type : str
        Object type, by default "individual".

    Returns
    -------
    tuple of (dict, int)
        Success message and HTTP status code.

    Raises
    ------
    NotFound
        If the individual does not exist.
    Forbidden
        If the user is not allowed to delete the individual.
    """
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

    The individual is also associated with the module `module_code` if it
    exists and is not already linked.

    Parameters
    ----------
    post_data : dict
        Data used to create or update an individual.
    module_code : str, optional
        Module code, by default "generic".

    Returns
    -------
    dict
        Serialized individual.
    """
    config = get_config(module_code, force=True)
    process_data = process_json_data_for_db_upsert(config, post_data, default_route_object_type)

    individual = MonitoringIndividualsSchema(unknown=EXCLUDE).load(process_data)

    # Association de l'individu au module courant (cor_individual_module)
    module = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == module_code)
    ).scalar_one_or_none()
    if module and module not in individual.modules:
        individual.modules.append(module)

    db.session.add(individual)
    db.session.commit()

    return MonitoringIndividualsSchema().dump(individual)
