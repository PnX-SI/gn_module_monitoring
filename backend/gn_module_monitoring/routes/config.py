from gn_module_monitoring.blueprint import blueprint_api
from gn_module_monitoring.config.repositories import get_config as get_old_config
from gn_module_monitoring.modules import get_module


@blueprint_api.route("/old/<string:module_code>/config", methods=["GET"])
@blueprint_api.route("/old/config", defaults={"module_code": None}, methods=["GET"])
def get_config_endpoint(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    config = get_old_config(module_code, force=True)
    return dict(config)


@blueprint_api.route("/<string:module_code>/config", methods=["GET"])
@blueprint_api.route("/config", defaults={"module_code": "generic"}, methods=["GET"])
def get_config(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    return get_module(module_code).dump_config()
