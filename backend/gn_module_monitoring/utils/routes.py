from typing import Tuple

from flask import Response, request
from flask.json import jsonify
from geonature.utils.env import DB
from gn_module_monitoring.modules.repositories import get_module
from gn_module_monitoring.utils.utils import to_int
from marshmallow import Schema
from sqlalchemy import cast, func, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Query
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.monitoring.queries import Query as MonitoringQuery
from gn_module_monitoring.monitoring.schemas import paginate_schema
from gn_module_monitoring.monitoring.definitions import monitoring_g_definitions


def get_limit_page(params: MultiDict) -> Tuple[int]:
    return int(params.pop("limit", 50)), int(params.pop("page", 1))


def get_sort(params: MultiDict, default_sort: str, default_direction) -> Tuple[str]:
    return params.pop("sort", default_sort), params.pop("sort_dir", default_direction)


def paginate(query: Query, schema: Schema, limit: int, page: int) -> Response:
    result = query.paginate(page=page, error_out=False, per_page=limit)
    pagination_schema = paginate_schema(schema)
    data = pagination_schema().dump(
        dict(items=result.items, count=result.total, limit=limit, page=page)
    )
    return jsonify(data)


def filter_params(query: MonitoringQuery, params: MultiDict) -> MonitoringQuery:
    if len(params) != 0:
        query = query.filter_by_params(params)
    return query


def sort(query: MonitoringQuery, sort: str, sort_dir: str) -> MonitoringQuery:
    if sort_dir in ["desc", "asc"]:
        query = query.sort(label=sort, direction=sort_dir)
    return query


def geojson_query(subquery) -> bytes:
    subquery_name = "q"
    subquery = subquery.alias(subquery_name)
    query = DB.session.query(
        func.json_build_object(
            text("'type'"),
            text("'FeatureCollection'"),
            text("'features'"),
            func.json_agg(cast(func.st_asgeojson(subquery), JSON)),
        )
    )
    result = query.first()
    if len(result) > 0:
        return result[0]
    return b""


def create_or_update_object_api_sites_sites_group(module_code, object_type, id=None):
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
        # TODO : A enlever une fois que le post_data contiendra geometry et type depuis le front
        if object_type == "site":
            post_data["geometry"] = {"type": "Point", "coordinates": [2.5, 50]}
            post_data["type"] = "Feature"
    # on rajoute id_module s'il n'est pas renseigné par défaut ??
    if "id_module" not in post_data["properties"]:
        module["id_module"] = "generic"
        post_data["properties"]["id_module"] = module["id_module"]
    else:
        post_data["properties"]["id_module"] = module.id_module

    return (
        monitoring_g_definitions.monitoring_object_instance(module_code, object_type, id)
        .create_or_update(post_data)
        .serialize(depth)
    )
