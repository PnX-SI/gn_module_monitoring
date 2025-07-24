import json

from flask import g, request
from flask.json import jsonify
from geonature.core.gn_commons.schemas import ModuleSchema
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures
from sqlalchemy import and_, select
from sqlalchemy.orm import Load, joinedload
from sqlalchemy.sql import func
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    cor_module_type,
    cor_site_type,
)
from gn_module_monitoring.monitoring.schemas import (
    BibTypeSiteSchema,
    MonitoringSitesSchema,
    add_specific_attributes,
)
from gn_module_monitoring.routes.modules import get_modules
from gn_module_monitoring.routes.monitoring import (
    create_or_update_object_api,
    get_serialized_object,
)
from gn_module_monitoring.utils.routes import (
    filter_params,
    geojson_query,
    get_limit_page,
    get_objet_with_permission_boolean,
    get_sort,
    paginate,
    paginate_scope,
    query_all_types_site_from_site_id,
    sort,
    sort_according_to_column_type_for_site,
)


@blueprint.route("/sites/config", methods=["GET"])
def get_config_sites(id=None, module_code="generic", object_type="site"):
    # A QUOI SERT CETTE ROUTE ?
    obj = get_serialized_object(module_code, object_type, id)
    return obj["properties"]


@blueprint.route("/sites/types", methods=["GET"])
def get_types_site():
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_nomenclature_type_site", default_direction="desc"
    )

    query = filter_params(BibTypeSite, query=select(BibTypeSite), params=params)
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
@blueprint.route(
    "/refacto/<string:module_code>/sites", methods=["GET"], defaults={"object_type": "site"}
)
@check_cruved_scope("R", object_code="MONITORINGS_SITES")
def get_sites(object_type, module_code=None):
    object_code = "MONITORINGS_SITES"
    params = MultiDict(request.args)
    limit, page = get_limit_page(params=params)
    sort_label, sort_dir = get_sort(
        params=params, default_sort="id_base_site", default_direction="desc"
    )

    query = select(TMonitoringSites)

    if module_code:
        query = query.where(
            TMonitoringSites.modules.any(TMonitoringModules.module_code == module_code)
        )

    config = get_config(g.current_module.module_code)
    specific_properties = config.get("site", {}).get("specific", {})

    query = filter_params(TMonitoringSites, query=query, params=params)
    query = sort_according_to_column_type_for_site(
        query, sort_label, sort_dir, specific_properties
    )

    query_allowed = TMonitoringSites.filter_by_readable(
        query=query, object_code=object_code, module_code=g.current_module.module_code
    )

    query_allowed = TMonitoringSites.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=specific_properties,
    )

    if module_code:
        schema = add_specific_attributes(MonitoringSitesSchema, object_type, module_code)
    else:
        schema = MonitoringSitesSchema

    return paginate_scope(
        query=query_allowed,
        schema=schema,
        limit=limit,
        page=page,
        object_code=object_code,
    )


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
@check_cruved_scope("R")
def get_all_site_geometries(object_type):
    return _get_site_geometries()


@blueprint.route(
    "/refacto/<string:module_code>/sites/geometries",
    methods=["GET"],
    defaults={"object_type": "site"},
)
@check_cruved_scope("R")
def get_module_site_geometries(object_type, module_code):
    return _get_site_geometries(module_code)


def _get_site_geometries(module_code=None):
    object_code = "MONITORINGS_SITES"
    # params = request.args.to_dict(flat=True)
    params = dict(**request.args)
    types_site = None
    if "types_site" in params:
        types_site = request.args.getlist("types_site")
        if not types_site[0].isdigit():
            # HACK gestionnaire des sites
            # Quand filtre sur type de site envoie une chaine de caractère
            params["types_site_label"] = types_site[0]
            params.pop("types_site")
            types_site = None
        else:
            params["types_site"] = types_site

    if g.current_module:
        module_code = g.current_module.module_code
    else:
        module_code = MODULE_CODE

    query = select(TMonitoringSites)
    query_allowed = TMonitoringSites.filter_by_readable(
        query=query, module_code=module_code, object_code=object_code
    )
    if module_code != MODULE_CODE:
        query_allowed = query_allowed.where(
            TMonitoringSites.modules.any(TMonitoringModules.module_code == module_code)
        )
    query_allowed = query_allowed.with_only_columns(
        TMonitoringSites.id_base_site,
        TMonitoringSites.base_site_name,
        TMonitoringSites.geom,
        TMonitoringSites.id_sites_group,
    ).distinct()
    query_allowed = TMonitoringSites.filter_by_params(query=query_allowed, params=params)

    config = get_config(module_code)

    query_allowed = TMonitoringSites.filter_by_specific(
        query=query_allowed,
        params=params,
        specific_properties=config.get("site", {}).get("specific", {}),
    )
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
        .options(Load(TMonitoringModules).raiseload("*"))  # bloque le chargement des relations
        .join(cor_module_type, cor_module_type.c.id_module == TMonitoringModules.id_module)
        .join(
            cor_site_type,
            and_(
                cor_site_type.c.id_type_site == cor_module_type.c.id_type_site,
                cor_site_type.c.id_base_site == id_base_site,
            ),
        )
        .where(TMonitoringModules.id_module.in_(ids_modules_allowed))
        .distinct()
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

    # get_config(module_code, force=True)

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

    # get_config(module_code, force=True)

    return create_or_update_object_api(module_code, object_type, _id), 201
