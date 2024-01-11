from flask import request, g
from flask.json import jsonify
import json
from geonature.core.gn_commons.schemas import ModuleSchema
from geonature.utils.env import db
from sqlalchemy import and_
from sqlalchemy.orm import Load, joinedload
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import select
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from geonature.core.gn_permissions import decorators as permissions
from pypnusershub.db.models import User
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config, get_config_with_specific
from gn_module_monitoring.monitoring.models import (
    BibTypeSite,
    TMonitoringModules,
    TMonitoringSites,
    TNomenclatures,
)
from gn_module_monitoring import MODULE_CODE
from geonature.core.gn_permissions.decorators import check_cruved_scope
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema
from gn_module_monitoring.routes.monitoring import (
    create_or_update_object_api,
    get_config_object,
)
from gn_module_monitoring.routes.modules import get_modules
from gn_module_monitoring.utils.routes import (
    filter_params,
    geojson_query,
    get_limit_page,
    get_sort,
    paginate,
    paginate_scope,
    sort,
    query_all_types_site_from_site_id,
    filter_according_to_column_type_for_site,
    sort_according_to_column_type_for_site,
    get_objet_with_permission_boolean,
)


@blueprint.route("/sites/config", methods=["GET"])
def get_config_sites(id=None, module_code="generic", object_type="site"):
    obj = get_config_object(module_code, object_type, id)
    return obj["properties"]


@blueprint.route("/sites/types", methods=["GET"])
def get_types_site():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_nomenclature_type_site", default_direction="desc"
    )

    query = filter_params(BibTypeSite, query=BibTypeSite.query, params=params)
    query = sort(query=query, model=BibTypeSite, sort=sort_label, sort_dir=sort_dir)

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

    query = (
        select(BibTypeSite)
        .join(BibTypeSite.nomenclature)
        .where(TNomenclatures.label_fr.ilike(f"%{params['label_fr']}%"))
    )
    if sort_dir == "asc":
        query = query.order_by(TNomenclatures.label_fr.asc())

    # See if there are not too much labels since they are used
    # in select in the frontend side. And an infinite select is not
    # implemented
    return paginate(
        query=query,
        schema=BibTypeSiteSchema,
        limit=limit,
        page=page,
    )


@blueprint.route("/sites/types/<int:id_type_site>", methods=["GET"])
def get_type_site_by_id(id_type_site):
    res = db.get_or_404(BibTypeSite, id_type_site)

    schema = BibTypeSiteSchema()
    return schema.dump(res)


@blueprint.route("/sites/<int:id_site>/types", methods=["GET"], defaults={"object_type": "site"})
def get_all_types_site_from_site_id(id_site, object_type):
    types_site = query_all_types_site_from_site_id(id_site)
    schema = BibTypeSiteSchema()
    return [schema.dump(res) for res in types_site]


@blueprint.route("/sites", methods=["GET"], defaults={"object_type": "site"})
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="MONITORINGS_SITES")
def get_sites(object_type):
    object_code = "MONITORINGS_SITES"
    params = MultiDict(request.args)
    # TODO: add filter support
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_base_site", default_direction="desc"
    )

    query = select(TMonitoringSites)
    query = filter_according_to_column_type_for_site(query, params)
    query = sort_according_to_column_type_for_site(query, sort_label, sort_dir)

    query_allowed = TMonitoringSites.filter_by_readable(query=query, object_code=object_code)
    return paginate_scope(
        query=query_allowed,
        schema=MonitoringSitesSchema,
        limit=limit,
        page=page,
        object_code=object_code,
    )
    # return paginate(
    #     query=query,
    #     schema=MonitoringSitesSchema,
    #     limit=limit,
    #     page=page,
    # )


@blueprint.route("/sites/<int:id>", methods=["GET"], defaults={"object_type": "site"})
@permissions.check_cruved_scope(
    "R", get_scope=True, module_code=MODULE_CODE, object_code="MONITORINGS_SITES"
)
def get_site_by_id(scope, id, object_type):
    site = db.get_or_404(TMonitoringSites, id)
    if not site.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot read site {site.id_base_site}")
    schema = MonitoringSitesSchema()
    response = schema.dump(site)
    response["cruved"] = get_objet_with_permission_boolean(
        [site], object_code="MONITORINGS_SITES"
    )[0]["cruved"]
    response["geometry"] = json.loads(response["geometry"])
    return response


@blueprint.route("/sites/geometries", methods=["GET"], defaults={"object_type": "site"})
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="MONITORINGS_SITES")
def get_all_site_geometries(object_type):
    object_code = "MONITORINGS_SITES"
    params = MultiDict(request.args)
    query = TMonitoringSites.query
    query_allowed = TMonitoringSites.filter_by_readable(query=query, object_code=object_code)
    query_allowed.with_entities(
        TMonitoringSites.id_base_site,
        TMonitoringSites.base_site_name,
        TMonitoringSites.geom,
        TMonitoringSites.id_sites_group,
    )
    query_allowed = TMonitoringSites.filter_by_params(query=query_allowed, params=params)
    subquery = query_allowed.subquery()

    result = geojson_query(subquery)

    return jsonify(result)


@blueprint.route("/sites/<int:id_base_site>/modules", methods=["GET"])
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="MONITORINGS_SITES")
def get_module_by_id_base_site(id_base_site: int):
    modules_object = get_modules()
    modules = get_objet_with_permission_boolean(
        modules_object, object_code="MONITORINGS_VISITES", depth=0
    )
    ids_modules_allowed = [module["id_module"] for module in modules if module["cruved"]["R"]]

    query = (
        select(TMonitoringModules)
        .options(
            Load(TMonitoringModules).raiseload("*"),
            joinedload(TMonitoringModules.types_site).options(joinedload(BibTypeSite.sites)),
        )
        .where(
            and_(
                TMonitoringModules.id_module.in_(ids_modules_allowed),
                TMonitoringModules.types_site.any(
                    BibTypeSite.sites.any(id_base_site=id_base_site)
                ),
            )
        )
    )

    schema = ModuleSchema()
    result = db.session.scalars(query).all()
    # TODO: Is it usefull to put a limit here? Will there be more than 200 modules?
    # If limit here, implement paginated/infinite scroll on frontend side
    return [schema.dump(res) for res in result]


# TODO: vérfier si c'est utilisé
@blueprint.route("/sites/module/<string:module_code>", methods=["GET"])
def get_module_sites(module_code: str):
    # TODO: load with site_categories.json API
    return jsonify({"module_code": module_code})


@blueprint.route("/sites", methods=["POST"], defaults={"object_type": "site"})
@check_cruved_scope("C", module_code=MODULE_CODE, object_code="MONITORINGS_SITES")
def post_sites(object_type):
    module_code = "generic"
    object_type = "site"
    post_data = dict(request.get_json())

    get_config_with_specific(module_code, force=True, complements=post_data["dataComplement"])

    return create_or_update_object_api(module_code, object_type), 201


@blueprint.route("/sites/<int:_id>", methods=["DELETE"], defaults={"object_type": "site"})
@permissions.check_cruved_scope(
    "D", get_scope=True, module_code=MODULE_CODE, object_code="MONITORINGS_SITES"
)
def delete_site(scope, _id, object_type):
    site = db.get_or_404(TMonitoringSites, _id)
    if not site.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot delete site {site.id_base_site}")
    db.session.delete(site)
    db.session.commit()
    return {"success": "Item is successfully deleted"}, 200


@blueprint.route("/sites/<int:_id>", methods=["PATCH"], defaults={"object_type": "site"})
@permissions.check_cruved_scope(
    "U", get_scope=True, module_code=MODULE_CODE, object_code="MONITORINGS_SITES"
)
def patch_sites(scope, _id, object_type):
    site = db.get_or_404(TMonitoringSites, _id)
    if not site.has_instance_permission(scope=scope):
        raise Forbidden(f"User {g.current_user} cannot update site {site.id_base_site}")
    module_code = "generic"
    post_data = dict(request.get_json())

    get_config_with_specific(module_code, force=True, complements=post_data["dataComplement"])

    return create_or_update_object_api(module_code, object_type, _id), 201
