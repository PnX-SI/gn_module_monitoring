from flask import Response, g
from flask.json import jsonify

from typing import Tuple
from marshmallow import Schema
from werkzeug.datastructures import MultiDict
from sqlalchemy import cast, func, text, select, and_
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import load_only
from sqlalchemy.sql.expression import Select

from geonature.utils.env import DB
from geonature.core.gn_permissions.models import PermObject, PermissionAvailable
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.utils.errors import GeoNatureError

from pypnusershub.db.models import User
from pypnnomenclature.models import TNomenclatures

from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringSitesGroups,
    cor_site_type,
    TBaseSites,
    cor_module_type,
    TModules,
)
from gn_module_monitoring.monitoring.schemas import paginate_schema


def get_limit_page(params: MultiDict) -> Tuple[int]:
    return int(params.pop("limit", 50)), int(params.pop("page", 1))


def get_sort(params: MultiDict, default_sort: str, default_direction) -> Tuple[str]:
    return params.pop("sort", default_sort), params.pop("sort_dir", default_direction)


def paginate(query: Select, schema: Schema, limit: int, page: int) -> Response:
    result = DB.paginate(query, page=page, per_page=limit, error_out=False)
    pagination_schema = paginate_schema(schema)
    data = pagination_schema().dump(
        dict(items=result.items, count=result.total, limit=limit, page=page)
    )
    return jsonify(data)


def paginate_scope(
    query: Select, schema: Schema, limit: int, page: int, object_code=None
) -> Response:
    result = DB.paginate(query, page=page, per_page=limit, error_out=False)

    pagination_schema = paginate_schema(schema)

    datas_allowed = pagination_schema().dump(
        dict(items=result.items, count=result.total, limit=limit, page=page)
    )
    cruved_item_dict = get_objet_with_permission_boolean(result, object_code=object_code)
    for cruved_item in cruved_item_dict:
        for i, data in enumerate(datas_allowed["items"]):
            if data[data["pk"]] == cruved_item[data["pk"]]:
                datas_allowed["items"][i]["cruved"] = cruved_item["cruved"]
    return jsonify(datas_allowed)


def filter_params(model, query: Select, params: MultiDict) -> Select:
    if len(params) == 0:
        return query

    if getattr(model, "filter_by_params", None):
        return model.filter_by_params(query=query, params=params)
    else:
        raise GeoNatureError("filter_params : La requête n'a pas de méthode filter_by_params")


def sort(model, query: Select, sort: str, sort_dir: str) -> Select:
    if sort_dir not in ["desc", "asc"]:
        return query

    if getattr(query, "sort", None):
        return query.sort(label=sort, direction=sort_dir)

    if getattr(model, sort, None):
        order_by = getattr(model, sort)
        if sort_dir == "desc":
            order_by = order_by.desc()
        return query.order_by(order_by)


def geojson_query(subquery) -> bytes:
    subquery_name = "q"
    subquery = subquery.alias(subquery_name)
    query = select(
        func.json_build_object(
            text("'type'"),
            text("'FeatureCollection'"),
            text("'features'"),
            func.json_agg(cast(func.st_asgeojson(subquery), JSON)),
        )
    )
    result = DB.session.execute(query.limit(1)).first()
    if len(result) > 0:
        return result[0]
    return b""


def get_sites_groups_from_module_id(module_id: int):
    query = (
        select(TMonitoringSitesGroups)
        .options(
            # Load(TMonitoringSitesGroups).raiseload("*"),
            load_only(TMonitoringSitesGroups.id_sites_group)
        )
        .join(
            TMonitoringSites,
            TMonitoringSites.id_sites_group == TMonitoringSitesGroups.id_sites_group,
        )
        .join(cor_site_type, cor_site_type.c.id_base_site == TBaseSites.id_base_site)
        .join(
            BibTypeSite,
            BibTypeSite.id_nomenclature_type_site == cor_site_type.c.id_type_site,
        )
        .join(
            cor_module_type,
            cor_module_type.c.id_type_site == BibTypeSite.id_nomenclature_type_site,
        )
        .join(TModules, TModules.id_module == cor_module_type.c.id_module)
        .where(TModules.id_module == module_id)
    )
    return DB.session.scalars(query).all()


def query_all_types_site_from_site_id(id_site: int):
    query = (
        select(BibTypeSite)
        .join(
            cor_site_type,
            BibTypeSite.id_nomenclature_type_site == cor_site_type.c.id_type_site,
        )
        .join(TBaseSites, cor_site_type.c.id_base_site == TBaseSites.id_base_site)
        .where(cor_site_type.c.id_base_site == id_site)
    )

    return DB.session.scalars(query).unique().all()


def query_all_types_site_from_module_id(id_module: int):
    query = (
        select(BibTypeSite)
        .join(
            cor_module_type,
            BibTypeSite.id_nomenclature_type_site == cor_module_type.c.id_type_site,
        )
        .join(TModules, cor_module_type.c.id_module == TModules.id_module)
        .where(cor_module_type.c.id_module == id_module)
    )
    return DB.session.scalars(query).unique().all()


def filter_according_to_column_type_for_site(query, params):
    if "types_site" in params:
        params_types_site = params.pop("types_site")
        query = (
            query.join(TMonitoringSites.types_site)
            .join(BibTypeSite.nomenclature)
            .where(TNomenclatures.label_fr.ilike(f"%{params_types_site}%"))
        )
    elif "id_inventor" in params:
        params_inventor = params.pop("id_inventor")
        query = query.join(
            User,
            User.id_role == TMonitoringSites.id_inventor,
        ).where(User.nom_complet.ilike(f"%{params_inventor}%"))
    if len(params) != 0:
        query = filter_params(TMonitoringSites, query=query, params=params)

    # TODO: filter by observers

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
        query = sort(TMonitoringSites, query=query, sort=sort_label, sort_dir=sort_dir)

    # TODO: filter by observers

    return query


def get_object_list_monitorings():
    """
    récupère objets permissions liés au module MONITORINGS

    :return:
    """
    try:
        object_list_monitorings = DB.session.execute(
            select(
                PermObject.code_object,
            )
            .join(PermissionAvailable, PermissionAvailable.id_object == PermObject.id_object)
            .join(
                TModules,
                and_(
                    TModules.id_module == PermissionAvailable.id_module,
                    TModules.module_code == "MONITORINGS",
                ),
            )
            .group_by(PermObject.code_object)
        ).all()
        return object_list_monitorings
    except Exception as e:
        raise GeoNatureError("MONITORINGS - get_object_list_monitorings : {}".format(str(e)))


def get_objet_with_permission_boolean(
    objects, depth: int = 0, module_code=None, object_code=None, id_role=None
):
    if id_role is None:
        id_role = g.current_user.id_role
    objects_out = []
    for object in objects:
        if module_code:
            cruved_object = object._get_cruved_scope(
                module_code=module_code, object_code=object_code
            )
        elif hasattr(object, "module"):
            cruved_object = object._get_cruved_scope(
                module_code=object.module.module_code, object_code=object_code
            )
        elif hasattr(object, "module_code"):
            cruved_object = object._get_cruved_scope(
                module_code=object.module_code, object_code=object_code
            )
        else:
            cruved_object = object._get_cruved_scope(object_code=object_code)
        object_out = object.as_dict(depth=depth)

        if hasattr(object, "module_code"):
            object_out["cruved"] = object.get_permission_by_action(
                module_code=object.module_code, object_code=object_code
            )
        else:
            object_out["cruved"] = object.has_permission(cruved_object=cruved_object)
        objects_out.append(object_out)

    return objects_out
