import json
from copy import deepcopy

from flask import current_app

from gn_module_monitoring.blueprint import blueprint_api
from gn_module_monitoring.config.repositories import get_config as get_old_config
from gn_module_monitoring.config.entities.base import BaseEntityConfigSchema
from gn_module_monitoring.config import get_tree_entities, get_module_config


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

    module_config = get_module_config(module_code)

    # FIXME: avoid loads + dumps, mais permet de serialiser widget & store
    module_config = json.loads(
        current_app.json.dumps(current_app.config["MONITORINGS"]["modules"][module_code])
    )

    # retro-compat pour le front : on remet widget & store à plat
    for entity in get_tree_entities(module_config["tree"]):
        entity_config = module_config[entity]
        fields_config = entity_config["fields"]
        for field in list(fields_config):
            field_config = fields_config[field]
            widget = field_config.pop("widget")
            widget["type_widget"] = widget.pop("type")
            store = field_config.pop("store")
            store["type_util"] = store.pop("type")
            fields_config[field] = {
                **widget,
                **store,
                **field_config,
            }

    return module_config
