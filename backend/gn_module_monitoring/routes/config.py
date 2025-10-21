from utils_flask_sqla.response import json_resp

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config,get_config_v2


# TODO : Remove when new API for config is effective
@blueprint.route("/config/<string:module_code>", methods=["GET"])
@blueprint.route("/config", defaults={"module_code": None}, methods=["GET"])
@json_resp
def get_config_api(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    config = get_config(module_code, force=True)
    return dict(config)

# TODO : Remove /refacto when old API for fetching config is removed
@blueprint.route("/refacto/config/<string:module_code>", methods=["GET"])
@blueprint.route("/refacto/config", defaults={"module_code": None}, methods=["GET"])
@json_resp
def get_config_apiV2(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    config = get_config_v2(module_code, force=True)
    return dict(config)



