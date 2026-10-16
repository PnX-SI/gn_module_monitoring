import json

import marshmallow as ma

from gn_module_monitoring.command.utils import validate_json_file_protocol
from gn_module_monitoring.command.check.utils import get_object_types, wrap_errors
from gn_module_monitoring.config.entities import load_module_entity_config


def legacy_check(module_code):
    # Legacy checks
    _is_valid, errors = validate_json_file_protocol(module_code)
    yield from errors


def check_module_entity_config(module_code, module_tree, entity):
    try:
        return load_module_entity_config(module_code, module_tree, entity)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        yield e
    except ma.exceptions.ValidationError as e:
        yield e.messages


def check_module_entities_config(module_code, config):
    """
    Contrôle la validité des fichiers de definition du protocole.
    """

    total_error_count = wrap_errors("Définition du protocole", legacy_check(module_code))

    for entity in get_object_types(config["tree"]):
        # TODO: remplacer les templates (__MONITORINGS_PATH, etc.)
        error_count, entity_config = wrap_errors(
            f"Définition du protocole - {entity}",
            check_module_entity_config(module_code, config["tree"], entity),
            return_result=True,
        )
        if entity_config is not None:
            config[entity] = entity_config
        total_error_count += error_count

    return total_error_count
