import os
import re
from pathlib import Path
from typing import Tuple

from gn_module_monitoring.command.imports.constant import (
    ValidationFlag,
)
from gn_module_monitoring.command.imports.destination import upsert_bib_destination
from gn_module_monitoring.command.imports.entity import (
    get_entities_protocol,
    insert_entities,
    insert_entity_field_relations,
)
from gn_module_monitoring.command.imports.fields import insert_bib_field
from gn_module_monitoring.command.imports.protocol import (
    compute_protocol_diff,
    format_protocol_diff,
    get_protocol_data,
    is_protocol_diff_empty,
    update_protocol,
)
from gn_module_monitoring.command.imports.sql import (
    check_rows_exist_in_import_table,
    create_sql_import_table_protocol,
    transient_table_has_diff,
)
from gn_module_monitoring.command.imports.utils import ask_confirmation
import click
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError


from geonature.utils.env import DB
from geonature.core.gn_permissions.models import (
    PermissionAvailable,
)
from geonature.core.gn_commons.models import TModules
from geonature.core.imports.models import (
    Destination,
)


from gn_module_monitoring.config.utils import (
    json_from_file,
    SUB_MODULE_CONFIG_DIR,
)

from gn_module_monitoring.utils.utils import extract_keys
from gn_module_monitoring.modules.repositories import get_module, get_source_by_code, get_modules

"""
utils.py

fonctions pour les commandes du module monitoring
"""


def remove_monitoring_module(module_code):
    try:
        module = get_module("module_code", module_code)
    except Exception:
        print("le module n'existe pas")
        return

    # remove module in db
    try:
        # suppression des permissions disponibles pour ce module
        # txt = f"DELETE FROM gn_permissions.t_permissions_available WHERE id_module = {module.id_module}"
        stmt = delete(PermissionAvailable).where(PermissionAvailable.id_module == module.id_module)
        DB.session.execute(stmt)

        stmt = delete(TModules).where(TModules.id_module == module.id_module)
        DB.session.execute(stmt)

        stmt = delete(Destination).where(Destination.id_module == module.id_module)
        DB.session.execute(stmt)

        DB.session.commit()
    except IntegrityError:
        print("Impossible de supprimer le module car il y a des données associées")
        return
    except Exception as e:
        print("Impossible de supprimer le module")
        raise (e)

    print("Remove source {}".format("MONITORING_" + module_code.upper()))
    source = get_source_by_code("MONITORING_" + module_code.upper())
    DB.session.delete(source)
    DB.session.commit()
    # run specific sql TODO
    # remove nomenclature TODO


def installed_modules(session=None):
    return [
        {
            "module_code": module.module_code,
            "module_label": module.module_label,
            "module_desc": module.module_desc,
        }
        for module in get_modules(session)
    ]


def available_modules():
    """
    renvoie la liste des modules disponibles non encore installés
    """
    installed_module_codes = list(map(lambda x: x["module_code"], installed_modules()))
    available_modules_ = []
    for root, dirs, files in os.walk(SUB_MODULE_CONFIG_DIR, followlinks=True):
        for d in dirs:
            module_file = Path(root) / d / "module.json"
            if d in installed_module_codes or not module_file.exists():
                continue
            module = json_from_file(module_file)
            available_modules_.append({**module, "module_code": d})
        break
    return available_modules_


def extract_keys(test_dict, keys=[]):
    """
    Fonction permettant d'extraire de façon récursive les clés d'un dictionnaire.
    """
    for key, val in test_dict.items():
        keys.append(key)
        if isinstance(val, dict):
            extract_keys(val, keys)
    return keys


def process_module_import(module_data):
    """
    Pipeline complet pour insérer un protocole et ses données dans la base.

    Parameters
    ----------
    module_data : dict
        Données de la table gn_commons.t_modules du module à importer.

    """
    try:
        with DB.session.begin_nested():
            destination = upsert_bib_destination(module_data)
            id_destination = destination.id_destination
            module_code = module_data["module_code"]

            protocol_data, entity_hierarchy_map = get_protocol_data(module_code, id_destination)
            insert_bib_field(protocol_data)

            insert_entities(
                protocol_data, id_destination, entity_hierarchy_map, module_code=module_code
            )

            insert_entity_field_relations(protocol_data, id_destination, entity_hierarchy_map)

            create_sql_import_table_protocol(module_code, protocol_data)
            DB.session.commit()
    except Exception as e:
        DB.session.rollback()
        raise Exception(
            f"Erreur lors du traitement du module {module_data['module_code']}: {str(e)}"
        )


DATA_LOSS_WARNING = "La table d'importation contient des données. La mise à jour du protocole peut entraîner la perte de données."


def print_protocol_diff(module_code: str, diff: dict):
    """Affiche toutes les différences d'un `compute_protocol_diff`."""
    click.secho(f"Différences entre la configuration et la base pour {module_code} :", bold=True)
    for line in format_protocol_diff(diff):
        click.echo(f"- {line}")


def apply_protocol_diff(module_data, module_code: str, diff: dict) -> bool:
    """
    Applique les écarts d'un `compute_protocol_diff` (bib_fields, bib_entities, table transitoire),
    après avertissement éventuel sur les données de la table transitoire et confirmation.

    Returns
    -------
    bool
        True si la mise à jour a réussi, False si elle est annulée ou a échoué.
    """
    if check_rows_exist_in_import_table(module_code):
        click.secho(f"ATTENTION: {DATA_LOSS_WARNING}", fg="yellow")

    if not ask_confirmation():
        click.secho("Mise à jour annulée, aucune modification effectuée.", fg="red")
        return False

    return update_protocol(
        module_data,
        module_code,
        diff["fields"]["deleted"],
        update_label_only=diff["label"] is not None and not _has_structural_changes(diff),
        recreate_transient_table=transient_table_has_diff(diff["transient_table"]),
    )


def process_update_module_import(module_data, module_code: str):
    """
    Compare le protocole voulu à l'existant, affiche toutes les différences, puis les applique
    après confirmation.

    Returns
    -------
    True si mis à jour, False si annulé ou en erreur, None si rien à faire.
    """
    try:
        diff = compute_protocol_diff(module_code, module_data)
    except Exception as e:
        click.secho(f"Erreur lors de la comparaison du module {module_code}: {str(e)}", fg="red")
        return False

    if is_protocol_diff_empty(diff):
        click.secho(f"Le module {module_code} est déjà à jour", fg="yellow")
        return None

    print_protocol_diff(module_code, diff)
    return apply_protocol_diff(module_data, module_code, diff)


def validate_protocol_changes(module_code: str, module_data) -> Tuple[set, list, list]:
    """
    Valide les changements du protocole (compatibilité : même retour qu'avant).

    Cette fonction ne sert plus au flux `process_import` (voir `process_update_module_import`) :
    elle demande la confirmation sur les données de la table transitoire, puis calcule le diff.

    Returns
    -------
        - Flags indiquant les types des changements détectés.
        - Liste des messages (différences, avertissements).
        - Champs à supprimer.
    """
    flags = set()
    warnings = []
    try:
        if check_rows_exist_in_import_table(module_code):
            if not ask_confirmation(DATA_LOSS_WARNING + " Voulez-vous continuer ? (y/n): "):
                warnings.append(
                    "La table d'importation contient des données. Impossible de mettre à jour le protocole."
                )
                flags.add(ValidationFlag.INVALID)
                return flags, warnings, []

        diff = compute_protocol_diff(module_code, module_data)
        warnings.extend(format_protocol_diff(diff))

        if diff["label"] is not None:
            flags.add(ValidationFlag.LABEL)
        if _has_structural_changes(diff):
            flags.add(ValidationFlag.FIELDS)
        if len(flags) == 0:
            flags.add(ValidationFlag.NOTHING)
        return flags, warnings, diff["fields"]["deleted"]

    except Exception as e:
        flags.add(ValidationFlag.INVALID)
        warnings.append(f"Erreur lors de la validation du protocole: {str(e)}")
        return flags, warnings, []


def _has_structural_changes(diff: dict) -> bool:
    """Vrai si le diff contient autre chose que le libellé (champs, entités, table transitoire)."""
    return not is_protocol_diff_empty({**diff, "label": None})


def check_module_code_name(module_code: str) -> bool:
    """
    Check if the module code name is valid.
    Valid if :
        - less than 63 characters
        - starts with a letter
        - contains only letters, numbers, $ or _

    Args:
        module_code (str): The module code name to be checked.

    Returns:
        bool: True if the module code name is valid, False otherwise.
    """
    if re.fullmatch(r"^[a-zA-Z][a-zA-Z0-9_$]{0,62}$", module_code):
        return True
    return False
