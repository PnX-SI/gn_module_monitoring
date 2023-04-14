from flask import jsonify, request
from geonature.utils.env import db
from marshmallow import ValidationError
from sqlalchemy import func
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.modules.repositories import get_module
from gn_module_monitoring.monitoring.definitions import monitoring_g_definitions
from gn_module_monitoring.monitoring.models import TMonitoringSites, TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema
from gn_module_monitoring.utils.errors.errorHandler import InvalidUsage
from gn_module_monitoring.utils.routes import (
    create_or_update_object_api_sites_sites_group,
    filter_params,
    geojson_query,
    get_limit_page,
    get_sort,
    paginate,
    sort,
)
from gn_module_monitoring.utils.utils import to_int


@blueprint.route("/sites_groups", methods=["GET"])
def get_sites_groups():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
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


@blueprint.route("/sites_groups/<int:id_sites_group>", methods=["GET"])
def get_sites_group_by_id(id_sites_group: int):
    schema = MonitoringSitesGroupsSchema()
    result = TMonitoringSitesGroups.find_by_id(id_sites_group)
    return jsonify(schema.dump(result))


@blueprint.route("/sites_groups/geometries", methods=["GET"])
def get_sites_group_geometries():
    subquery = (
        db.session.query(
            TMonitoringSitesGroups.id_sites_group,
            TMonitoringSitesGroups.sites_group_name,
            func.st_convexHull(func.st_collect(TMonitoringSites.geom)),
        )
        .group_by(TMonitoringSitesGroups.id_sites_group, TMonitoringSitesGroups.sites_group_name)
        .join(
            TMonitoringSites,
            TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
        )
        .subquery()
    )

    result = geojson_query(subquery)

    return jsonify(result)


@blueprint.route("/sites_groups/<int:_id>", methods=["PATCH"])
def patch(_id):
    # ###############################""
    # FROM route/monitorings
    module_code = "generic"
    object_type = "sites_group"
    get_config(module_code, force=True)
    return create_or_update_object_api_sites_sites_group(module_code, object_type, _id), 201


@blueprint.route("/sites_groups/<int:_id>", methods=["DELETE"])
def delete(_id):
    item_schema = MonitoringSitesGroupsSchema()
    item = TMonitoringSitesGroups.find_by_id(_id)
    TMonitoringSitesGroups.query.filter_by(id_g=_id).delete()
    db.session.commit()
    return item_schema.dump(item), 201


@blueprint.route("/sites_groups", methods=["POST"])
def post():
    module_code = "generic"
    object_type = "sites_group"
    get_config(module_code, force=True)
    return create_or_update_object_api_sites_sites_group(module_code, object_type), 201


@blueprint.errorhandler(ValidationError)
def handle_validation_error(error):
    return InvalidUsage(
        "Fields cannot be validated, message : {}".format(error.messages),
        status_code=422,
        payload=error.data,
    ).to_dict()


# TODO: OPTIMIZE in order to adapt to new monitoring module (entry by sites_groups)


def create_or_update_object_api(module_code, object_type, id=None):
    """
    route pour la création ou la modification d'un objet
    si id est renseigné, c'est une création (PATCH)
    sinon c'est une modification (POST)

    :param module_code: reference le module concerne
    :param object_type: le type d'object (site, visit, obervation)
    :param id : l'identifiant de l'object (de id_base_site pour site)
    :type module_code: str
    :type object_type: str
    :type id: int
    :return: renvoie l'object crée ou modifié
    :rtype: dict
    """
    depth = to_int(request.args.get("depth", 1))

    # recupération des données post
    post_data = dict(request.get_json())
    if module_code != "generic":
        module = get_module("module_code", module_code)
    else:
        module = {"id_module": "generic"}
        #TODO : A enlever une fois que le post_data contiendra geometry et type depuis le front
        if object_type == "site":
            post_data["geometry"]={'type':'Point', 'coordinates':[2.5,50]}
            post_data["type"]='Feature'
    # on rajoute id_module s'il n'est pas renseigné par défaut ??
    if "id_module" not in post_data["properties"]:
        module["id_module"] = "generic"
        post_data["properties"]["id_module"] = module["id_module"]
    else:
        post_data["properties"]["id_module"] = module["id_module"]

    return (
        monitoring_g_definitions.monitoring_object_instance(module_code, object_type, id)
        .create_or_update(post_data)
        .serialize(depth)
    )
