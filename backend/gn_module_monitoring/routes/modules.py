"""
    routes pour les modules de suivis...
"""

from flask import request
from utils_flask_sqla.response import json_resp_accept_empty_list, json_resp

from geonature.core.gn_permissions.tools import get_scopes_by_action, has_any_permissions_by_action
from geonature.core.gn_permissions.decorators import check_cruved_scope

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.modules.repositories import (
    get_module,
    get_modules,
)
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.utils.routes import (
    query_all_types_site_from_module_id,
    get_object_list_monitorings,
)


@blueprint.route("/module/<int:value>", methods=["GET"])
@check_cruved_scope("R", module_code=MODULE_CODE)
@json_resp
def get_module_api(value):
    """
    Renvoie un module référencé par son champ module_code
    par default cherche par id_module
    on peut preciser field_name en parametre de requete GET
    ?field_name=module_code pour avoir unmodule depuis son champs module_code
    """

    depth = to_int(request.args.get("depth", 0))
    field_name = request.args.get("field_name", "id_module")

    module = get_module(field_name, value)
    module_out = []
    if module:
        module_out = module.as_dict(depth=depth)
        module_out["cruved"] = get_scopes_by_action(
            module_code=module.module_code, object_code="MONITORINGS_MODULES"
        )

    return module_out


@blueprint.route("/cruved_object", methods=["GET"])
@check_cruved_scope("R", module_code=MODULE_CODE)
def get_cruved_monitorings():
    """
    Renvoie la liste des modules de suivi
    """
    dic_object_cruved = {}
    object_list_tuples = get_object_list_monitorings()
    object_list = [value for (value,) in object_list_tuples]
    for object in object_list:
        dic_object_cruved[object] = has_any_permissions_by_action(
            module_code=MODULE_CODE, object_code=object
        )

    return dic_object_cruved


@blueprint.route("/modules", methods=["GET"])
@check_cruved_scope("R", module_code=MODULE_CODE)
@json_resp_accept_empty_list
def get_modules_api():
    """
    Renvoie la liste des modules de suivi
    """

    depth = to_int(request.args.get("depth", 0))

    modules_out = []
    modules = get_modules()
    for module in modules:
        module_out = module.as_dict(depth=depth)
        module_out["cruved"] = get_scopes_by_action(
            module_code=module.module_code, object_code="MONITORINGS_MODULES"
        )

        modules_out.append(module_out)

    return modules_out


# TODEL ?
@blueprint.route("/modules/<string:module_code>/types_sites", methods=["GET"])
def get_all_types_site_from_module_id(module_code):
    module = get_module("module_code", module_code)
    id_module = None
    if module:
        id_module = module.id_module
    types_site = query_all_types_site_from_module_id(id_module)
    schema = BibTypeSiteSchema()
    return [schema.dump(res) for res in types_site]
