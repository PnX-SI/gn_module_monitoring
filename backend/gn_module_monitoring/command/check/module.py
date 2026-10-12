import json

from marshmallow import ValidationError

from gn_module_monitoring.config.module import load_module_config


def check_module_config(module_code):
    try:
        return load_module_config(module_code)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        yield e
    except ValidationError as e:
        yield e.messages
