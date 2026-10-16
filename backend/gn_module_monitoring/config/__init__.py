from .utils import get_data_preload, get_tree_entities
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
    config["module"] = load_module_db_config(module_code)
    substitutions = {f"__MODULE.{k.upper()}": v for k, v in config["module"].items()}
    for entity in get_tree_entities(config["tree"]):
        config[entity] = load_module_entity_config(
            module_code, config["tree"], entity=entity, substitutions=substitutions
        )
    config["nomenclature"] = get_data_preload(config)["nomenclature"]
