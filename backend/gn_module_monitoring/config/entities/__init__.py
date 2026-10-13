import json

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.services import SERVICE_MAP


def load_module_entity_config(module_code, entity):
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
    schema = SERVICE_MAP[entity].config_schema()
    with schema_context(entity=entity):
        return schema.load(entity_config)
