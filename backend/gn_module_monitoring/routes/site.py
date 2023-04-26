from flask import request
from flask.json import jsonify
from geonature.core.gn_commons.schemas import ModuleSchema
from geonature.utils.env import db
from sqlalchemy.orm import Load, joinedload
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    BibTypeSite,
    TMonitoringModules,
    TMonitoringSites,
    TNomenclatures,
)
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema
from gn_module_monitoring.routes.monitoring import create_or_update_object_api_sites_sites_group
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


@blueprint.route("/sites/types/label", methods=["GET"])
def get_types_site_by_label():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="label_fr", default_direction="desc"
    )
    joinquery = BibTypeSite.query.join(BibTypeSite.nomenclature).filter(
        TNomenclatures.label_fr.ilike(f"%{params['label_fr']}%")
    )
    if sort_dir == "asc":
        joinquery = joinquery.order_by(TNomenclatures.label_fr.asc())

    # See if there are not too much labels since they are used
    # in select in the frontend side. And an infinite select is not
    # implemented
    return paginate(
        query=joinquery,
        schema=BibTypeSiteSchema,
        limit=limit,
        page=page,
    )


@blueprint.route("/sites/types/<int:id_type_site>", methods=["GET"])
def get_type_site_by_id(id_type_site):
    res = BibTypeSite.find_by_id(id_type_site)
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


@blueprint.route("/sites/<int:id_base_site>", methods=["GET"])
def get_site_by_id(id_base_site):
    site = TMonitoringSites.query.get_or_404(id_base_site)
    schema = MonitoringSitesSchema()
    return schema.dump(site)


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


@blueprint.route("/sites/<int:id_base_site>/modules", methods=["GET"])
def get_module_by_id_base_site(id_base_site: int):
    query = TMonitoringModules.query.options(
        Load(TMonitoringModules).raiseload("*"),
        joinedload(TMonitoringModules.types_site).options(joinedload(BibTypeSite.sites)),
    ).filter(TMonitoringModules.types_site.any(BibTypeSite.sites.any(id_base_site=id_base_site)))

    result = query.all()
    schema = ModuleSchema()
    # TODO: Is it usefull to put a limit here? Will there be more than 200 modules?
    # If limit here, implement paginated/infinite scroll on frontend side
    return [schema.dump(res) for res in result]


@blueprint.route("/sites/module/<string:module_code>", methods=["GET"])
def get_module_sites(module_code: str):
    # TODO: load with site_categories.json API
    return jsonify({"module_code": module_code})


@blueprint.route("/sites", methods=["POST"])
def post_sites():
    module_code = "generic"
    object_type = "site"
    customConfig = dict()
    post_data = dict(request.get_json())
    for keys in post_data["dataComplement"].keys():
        if "config" in post_data["dataComplement"][keys]:
            customConfig.update(post_data["dataComplement"][keys]["config"])
    get_config(module_code, force=True, customSpecConfig=customConfig)
    return create_or_update_object_api_sites_sites_group(module_code, object_type), 201


@blueprint.route("/sites/<int:_id>", methods=["DELETE"])
def delete_site(_id):
    item = TMonitoringSites.find_by_id(_id)
    db.session.delete(item)
    db.session.commit()
    return {
        "success": f"Item with {item.id_g} from table {item.__tablename__} is successfully deleted"
    }, 200

@blueprint.route("/sites/<int:_id>", methods=["PATCH"])
def patch_sites(_id):
    module_code = "generic"
    object_type = "site"
    customConfig = dict()
    post_data = dict(request.get_json())
    for keys in post_data["dataComplement"].keys():
        if "config" in post_data["dataComplement"][keys]:
            customConfig.update(post_data["dataComplement"][keys]["config"])
    get_config(module_code, force=True, customSpecConfig=customConfig)
    return create_or_update_object_api_sites_sites_group(module_code, object_type, _id), 201
