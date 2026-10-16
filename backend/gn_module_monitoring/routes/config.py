from utils_flask_sqla.response import json_resp

from gn_module_monitoring.blueprint import blueprint_api
from gn_module_monitoring.config.repositories import get_config


@blueprint_api.route("/<string:module_code>/config", methods=["GET"])
@blueprint_api.route("/config", defaults={"module_code": None}, methods=["GET"])
@json_resp
def get_config_apiV2(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    config = get_config(module_code, force=True)
    return dict(config)
