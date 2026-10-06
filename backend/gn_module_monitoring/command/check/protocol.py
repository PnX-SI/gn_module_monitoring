import click

from gn_module_monitoring.command.utils import validate_json_file_protocol


def check_module_protocol(module_code):
    """
    Contrôle la validité des fichiers de definition du protocole.
    Retourne le nombre d'erreurs détectées.
    """
    # TODO: do better checks as validate_json_file_protocol do not check a lot of things…
    _is_valid, errors = validate_json_file_protocol(module_code)
    yield from errors
