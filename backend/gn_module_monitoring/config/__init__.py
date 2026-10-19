import sqlalchemy as sa

from geonature.utils.env import db
from geonature.utils.config import config

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.monitoring.models import TMonitoringModules

from .utils import (
    get_data_preload,
    get_substitutions,
    get_tree_entities,
    json_config_from_db,
    is_module_configured,
)
from .main import load_module_root_config, load_module_db_config
from .entities import load_module_entity_config


def load_module_config(module_code):
    """
    Charge la configuration d’un module monitoring.

    Le chargement s’effectue en 5 phases :
    - Chargement de config.json
    - Chargement de config["module"] à partir des attributs de t_module_complements
    - Calcul des variables de substitutions (__MODULE.XXX) à partir de config["module"]
    - Chargement des entités (sites_group.json, site.json, visit.json, etc.) en appliquant les substitutions
    - Calcul de data["nomenclature"]
    """
    config = load_module_root_config(module_code)
    if module_code == "generic":
        config["configured"] = True
        module_db_config = {}
        substitutions = {}
    else:
        module = db.session.execute(
            sa.select(TMonitoringModules).where(TMonitoringModules.module_code == module_code)
        ).scalar_one()
        config["configured"] = is_module_configured(module)
        module_db_config = load_module_db_config(module)
        substitutions = get_substitutions(module_db_config)
    entities = get_tree_entities(config["tree"])
    for entity in entities:
        entity_config = load_module_entity_config(
            module_code, config["tree"], entity=entity, substitutions=substitutions
        )
        if entity == "module":
            # config["module"] combine les attributs de la base et la config module.json
            # FIXME: does module_db_config is really required to be merged? quid of generic?
            entity_config = {**module_db_config, **entity_config}
        config[entity] = entity_config

    # parent_types / children_types de chaque type d'objet (attendus par le frontend)
    for entity in entities:
        config[entity]["parent_types"] = config["parent_types"].get(entity, [])
        config[entity]["children_types"] = config["children_types"].get(entity, [])
        if not config[entity]["parent_types"] and config[entity]["children_types"]:
            config[entity]["root_object"] = True

    # types de site du module, attendus par le frontend (config.module.types_site)
    # et par les objets site (config.site.types_site) : {id_nomenclature_type_site: {name}}
    types_site = json_config_from_db(module_code)["types_site"]
    config["module"]["types_site"] = types_site
    if "site" in config:
        config["site"]["types_site"] = types_site

    config["nomenclature"] = get_data_preload(config)["nomenclature"]
    return config


def get_module_config(module_code):
    monitoring_config = config[MODULE_CODE]
    monitoring_config.setdefault("modules", {})
    if "module_code" not in monitoring_config["modules"]:
        monitoring_config["modules"][module_code] = load_module_config(module_code)
    return monitoring_config["modules"][module_code]
