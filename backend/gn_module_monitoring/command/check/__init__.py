import json

import click
from flask import current_app
from marshmallow import ValidationError

from gn_module_monitoring.modules import MonitoringModule
from gn_module_monitoring.command.check.data import check_module_data
from gn_module_monitoring.command.check.nomenclature import check_module_nomenclatures
from gn_module_monitoring.command.check.sql import check_module_sql_files
from gn_module_monitoring.command.check.permissions import check_module_permissions
from gn_module_monitoring.command.check.utils import wrap_errors
from gn_module_monitoring.command.utils import available_modules, installed_modules
from gn_module_monitoring.tools.utils import schema_context


def load_module(module_code):
    try:
        return MonitoringModule(module_code)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        yield e
    except ValidationError as e:
        yield e.messages


def run_module_check(module_code, installed, check_data, data_filters, fix):
    total_error_count = 0

    total_error_count += wrap_errors(
        "Nomenclatures", check_module_nomenclatures(module_code, check_data, fix)
    )

    total_error_count += check_module_sql_files(module_code, check_data, fix)

    if installed:
        error_count, module = wrap_errors(
            "Assemblage des configurations", load_module(module_code), return_result=True
        )
        total_error_count += error_count

        if module is not None and check_data:
            total_error_count += wrap_errors("Permissions", check_module_permissions(module_code))

            total_error_count += check_module_data(module, fix, data_filters)

    return total_error_count


def run_check(module_code, strict, check_data, data_filters, fix):
    current_app.config["MONITORINGS"]["STRICT"] = strict

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

        installed = module_code in installed_module_codes
        with schema_context(protocol_installed=installed):
            error_count += run_module_check(
                module_code,
                installed,
                check_data and installed,
                data_filters,
                fix,
            )

    click.echo("")
    if error_count:
        click.secho(f"{error_count} anomalie(s) détectée(s)", fg="red", bold=True)
    else:
        click.secho("Aucune anomalie détectée", fg="green", bold=True)
