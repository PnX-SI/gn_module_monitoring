from flask import request
from flask.json import jsonify
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.monitoring.models import BibTypeSite, TMonitoringSites
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema
from gn_module_monitoring.utils.routes import (
    filter_params,
    geojson_query,
    get_limit_page,
    get_sort,
    paginate,
    sort,
)


@blueprint.route("/sites/types", methods=["GET"])
def get_types_site():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_nomenclature_type_site", default_direction="desc"
    )

    query = filter_params(query=BibTypeSite.query, params=params)
    query = sort(query=query, sort=sort_label, sort_dir=sort_dir)

    return paginate(
        query=query,
        schema=BibTypeSiteSchema,
        limit=limit,
        page=page,
    )


@blueprint.route("/sites/types/<int:id_type_site>", methods=["GET"])
def get_type_site_by_id(id_type_site):
    query = BibTypeSite.query.filter_by(id_nomenclature_type_site=id_type_site)
    res = query.first()
    schema = BibTypeSiteSchema()
    return schema.dump(res)


@blueprint.route("/sites", methods=["GET"])
def get_sites():
    params = MultiDict(request.args)
    # TODO: add filter support
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_base_site", default_direction="desc"
    )
    query = TMonitoringSites.query
    query = filter_params(query=query, params=params)
    query = sort(query=query, sort=sort_label, sort_dir=sort_dir)
    return paginate(
        query=query,
        schema=MonitoringSitesSchema,
        limit=limit,
        page=page,
    )


@blueprint.route("/sites/geometries", methods=["GET"])
def get_all_site_geometries():
    params = MultiDict(request.args)
    subquery = (
        TMonitoringSites.query.with_entities(
            TMonitoringSites.id_base_site,
            TMonitoringSites.base_site_name,
            TMonitoringSites.geom,
            TMonitoringSites.id_sites_group,
        )
        .filter_by_params(params)
        .subquery()
    )

    result = geojson_query(subquery)

    return jsonify(result)


@blueprint.route("/sites/module/<string:module_code>", methods=["GET"])
def get_module_sites(module_code: str):
    # TODO: load with site_categories.json API
    return jsonify({"module_code": module_code})
