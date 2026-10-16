import json

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.services import SERVICE_MAP


def load_module_entity_config(module_code, module_tree, entity):
    """
    Raises:
        UnicodeDecodeError
        JSONDecodeError
        ValidationError
    """
    config_path = monitoring_module_config_path(module_code) / f"{entity}.json"
    if config_path.is_file():
        with config_path.open() as f:
            entity_config = json.load(f)
    else:
        entity_config = {}

    #     # TODO: remplacer les templates (__MONITORINGS_PATH, etc.)
    entity_service = SERVICE_MAP[entity]
    with schema_context(entity_service=entity_service):
        return entity_service.config_schema(module_tree=module_tree).load(entity_config)
