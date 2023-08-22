from typing import Tuple

from flask import Response
from flask.json import jsonify
from geonature.utils.env import DB
from pypnusershub.db.models import User
from gn_module_monitoring.monitoring.models import (
    BibTypeSite,
    TMonitoringSites,
    TMonitoringSitesGroups,
    cor_type_site,
    TBaseSites,
    cor_module_type,
    TModules,
    TNomenclatures,
)
from marshmallow import Schema
from sqlalchemy import cast, func, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Query, load_only
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.monitoring.queries import Query as MonitoringQuery
from gn_module_monitoring.monitoring.schemas import paginate_schema


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


def get_sites_groups_from_module_id(module_id: int):
    # query = TMonitoringSitesGroups.query.options(
    #     # Load(TMonitoringSitesGroups).raiseload("*"),
    #     load_only(TMonitoringSitesGroups.id_sites_group),
    #     joinedload(TMonitoringSitesGroups.sites).options(
    #         joinedload(TMonitoringSites.types_site).options(joinedload(BibTypeSite.modules))
    #     ),
    # ).filter(TMonitoringModules.id_module == module_id)

    query = (
        TMonitoringSitesGroups.query.options(
            # Load(TMonitoringSitesGroups).raiseload("*"),
            load_only(TMonitoringSitesGroups.id_sites_group)
        )
        .join(
            TMonitoringSites,
            TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
        )
        .join(cor_type_site, cor_type_site.c.id_base_site == TBaseSites.id_base_site)
        .join(
            BibTypeSite,
            BibTypeSite.id_nomenclature_type_site == cor_type_site.c.id_type_site,
        )
        .join(
            cor_module_type,
            cor_module_type.c.id_type_site == BibTypeSite.id_nomenclature_type_site,
        )
        .join(TModules, TModules.id_module == cor_module_type.c.id_module)
        .filter(TModules.id_module == module_id)
    )

    return query.all()


def query_all_types_site_from_site_id(id_site: int):
    query = (
        BibTypeSite.query.join(
            cor_type_site,
            BibTypeSite.id_nomenclature_type_site == cor_type_site.c.id_type_site,
        )
        .join(TBaseSites, cor_type_site.c.id_base_site == TBaseSites.id_base_site)
        .filter(cor_type_site.c.id_base_site == id_site)
    )
    return query.all()


def query_all_types_site_from_module_id(id_module: int):
    query = (
        BibTypeSite.query.join(
            cor_module_type,
            BibTypeSite.id_nomenclature_type_site == cor_module_type.c.id_type_site,
        )
        .join(TModules, cor_module_type.c.id_module == TModules.id_module)
        .filter(cor_module_type.c.id_module == id_module)
    )
    return query.all()


def filter_according_to_column_type_for_site(query, params):
    if "types_site" in params:
        params_types_site = params.pop("types_site")
        query = (
            query.join(TMonitoringSites.types_site)
            .join(BibTypeSite.nomenclature)
            .filter(TNomenclatures.label_fr.ilike(f"%{params_types_site}%"))
        )
    elif "id_inventor" in params:
        params_inventor = params.pop("id_inventor")
        query = query.join(
            User,
            User.id_role == TMonitoringSites.id_inventor,
        ).filter(User.nom_complet.ilike(f"%{params_inventor}%"))
    if len(params) != 0:
        query = filter_params(query=query, params=params)

    return query


def sort_according_to_column_type_for_site(query, sort_label, sort_dir):
    if sort_label == "types_site":
        if sort_dir == "asc":
            query = query.order_by(TNomenclatures.label_fr.asc())
        else:
            query = query.order_by(TNomenclatures.label_fr.desc())
    elif sort_label == "id_inventor":
        if sort_dir == "asc":
            query = query.order_by(User.nom_complet.asc())
        else:
            query = query.order_by(User.nom_complet.desc())
    else:
        query = sort(query=query, sort=sort_label, sort_dir=sort_dir)
    return query
