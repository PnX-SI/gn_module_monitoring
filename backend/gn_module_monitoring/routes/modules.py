"""
routes pour les modules de suivis...
"""

from flask import request
from utils_flask_sqla.response import json_resp_accept_empty_list, json_resp

from marshmallow import EXCLUDE

from geonature.utils.env import db
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.tools import get_scopes_by_action
from geonature.core.gn_permissions.decorators import check_cruved_scope

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringModuleSchema
from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.modules.repositories import (
    get_module,
    get_modules,
)
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.utils.utils import to_int
from gn_module_monitoring.utils.routes import (
    query_all_types_site_from_module_id,
    process_json_data_for_db_upsert,
)


@blueprint.route("/module/<value>", methods=["GET"])
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="ALL")
@json_resp
def get_module_api(value):
    """
    Renvoie un module référencé par son champ module_code
    par default cherche par id_module
    on peut preciser field_name en parametre de requete GET
    ?field_name=module_code pour avoir unmodule depuis son champs module_code
    """

    field_name = request.args.get("field_name", "id_module")

    module = get_module(field_name, value)
    module_out = []
    if module:
        module_out = MonitoringModuleSchema().dump(module)
        module_out["cruved"] = get_scopes_by_action(
            module_code=module.module_code, object_code="MONITORINGS_MODULES"
        )

    return module_out


@blueprint.route("/modules", methods=["GET"])
@check_cruved_scope("R", module_code=MODULE_CODE, object_code="ALL")
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
    schema = BibTypeSiteSchema(many=True)
    return schema.dump(types_site)


@blueprint.route("/module/<int:_id>", methods=["PATCH"], defaults={"object_type": "module"})
@blueprint.route(
    "/<string:module_code>/module/<int:_id>",
    methods=["PATCH"],
    defaults={"object_type": "module"},
)
@permissions.check_cruved_scope("U", get_scope=True, object_code="MONITORINGS_MODULES")
def patch_module(scope, object_type: str, module_code: str = "generic", _id: int = None):
    module = db.get_or_404(TMonitoringModules, _id)
    post_data = dict(request.get_json())
    module = create_or_update_module(post_data, module_code)
    return module


def create_or_update_module(post_data: dict, module_code: str):
    """
    Create or update a module.

    :param post_data: dict containing data to create or update a module
    :param module_code: str, module code, default is "generic"
    :return: dict, serialized module
    """
    config = get_config(module_code, force=True)
    process_data = process_json_data_for_db_upsert(config, post_data, "module")
    sites_group = MonitoringModuleSchema(unknown=EXCLUDE).load(process_data)
    db.session.add(sites_group)
    db.session.commit()
    return MonitoringModuleSchema().dump(sites_group)
