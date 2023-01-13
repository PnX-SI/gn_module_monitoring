from flask import request
from flask.json import jsonify
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.monitoring.models import BibTypeSite, TMonitoringSites
from gn_module_monitoring.utils.routes import (
    filter_params,
    get_limit_offset,
    get_sort,
    paginate,
    sort,
)
from gn_module_monitoring.monitoring.schemas import MonitoringSitesSchema,BibTypeSiteSchema


@blueprint.route("/sites/types", methods=["GET"])
def get_types_site():
    params = MultiDict(request.args)
    limit, page = get_limit_offset(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_nomenclature", default_direction="desc"
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
    query = BibTypeSite.query.filter_by(id_nomenclature=id_type_site)
    res = query.first()
    schema = BibTypeSiteSchema()
    return schema.dump(res)


@blueprint.route("/sites", methods=["GET"])
def get_sites():
    params = MultiDict(request.args)
    # TODO: add filter support
    limit, page = get_limit_offset(params=params)
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


@blueprint.route("/sites/module/<string:module_code>", methods=["GET"])
def get_module_sites(module_code: str):
    # TODO: load with site_categories.json API
    return jsonify({"module_code": module_code})
