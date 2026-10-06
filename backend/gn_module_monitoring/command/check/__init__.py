import click

from gn_module_monitoring.command.check.protocol import check_module_protocol
from gn_module_monitoring.command.check.config import check_module_config
from gn_module_monitoring.command.check.data import check_module_data
from gn_module_monitoring.command.check.nomenclature import check_module_nomenclatures
from gn_module_monitoring.command.check.sql import check_module_sql_files

from gn_module_monitoring.command.check.utils import wrap_errors
from gn_module_monitoring.command.utils import (
    available_modules,
    installed_modules,
)


def check_module_permissions(module_code):
    return
    yield


def run_module_check(module_code, check_data, data_filters, fix):
    total_error_count = 0

    error_count, _ = wrap_errors(
        "Fichiers de définition du protocole", check_module_protocol(module_code)
    )
    total_error_count += error_count

    error_count, _ = wrap_errors(
        "Nomenclatures", check_module_nomenclatures(module_code, check_data, fix)
    )
    total_error_count += error_count

    total_error_count += check_module_sql_files(module_code, check_data, fix)

    error_count, config = wrap_errors("Configuration", check_module_config(module_code))
    total_error_count += error_count
    if not config:  # can not run data checks without valid config
        return total_error_count

    if check_data:
        error_count, _ = wrap_errors("Permissions", check_module_permissions(module_code))
        total_error_count += error_count

        total_error_count += check_module_data(config, fix, data_filters)

    return total_error_count


def run_check(module_code, check_data, data_filters, fix):
    available_module_codes = {module["module_code"] for module in available_modules()}
    installed_module_codes = {module["module_code"] for module in installed_modules()}

    if module_code:
        if module_code not in available_module_codes | installed_module_codes:
            raise click.BadArgumentUsage(message=f"Le module '{module_code}' n’existe pas !")
        module_codes = [module_code]
    else:
        module_codes = sorted(available_module_codes | installed_module_codes)

    if not module_codes:
        click.secho("Aucun protocole de suivi", fg="yellow")
        return

    error_count = 0
    for module_code in module_codes:
        click.secho(f"===== {module_code} =====", bold=True)
        _check_data = check_data and module_code in installed_module_codes

        error_count += run_module_check(module_code, _check_data, data_filters, fix)

    click.echo("")
    if error_count:
        click.secho(f"{error_count} anomalie(s) détectée(s)", fg="red", bold=True)
    else:
        click.secho("Aucune anomalie détectée", fg="green", bold=True)
