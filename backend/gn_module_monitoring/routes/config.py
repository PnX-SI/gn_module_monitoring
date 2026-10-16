from flask import current_app

from gn_module_monitoring.blueprint import blueprint_api
from gn_module_monitoring.config.repositories import get_config


@blueprint_api.route("/old/<string:module_code>/config", methods=["GET"])
@blueprint_api.route("/old/config", defaults={"module_code": None}, methods=["GET"])
def get_config_endpoint(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    config = get_config(module_code, force=True)
    return dict(config)


@blueprint_api.route("/<string:module_code>/config", methods=["GET"])
def get_config(module_code):
    """
    route qui renvoie la config pour un module donné
    """
    module_config = current_app.config["MONITORINGS"]["protocols"][module_code]
    print(module_config)
    return module_config
