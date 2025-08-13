import os
from pathlib import Path

from gn_module_monitoring.command.imports.constant import TYPE_WIDGET
from gn_module_monitoring.command.imports.destination import upsert_bib_destination
from gn_module_monitoring.command.imports.entity import (
    get_entities_protocol,
    insert_entities,
    insert_entity_field_relations,
)
from gn_module_monitoring.command.imports.fields import insert_bib_field
from gn_module_monitoring.command.imports.protocol import (
    compare_protocol_fields,
    get_existing_protocol_state,
    get_protocol_data,
    update_protocol,
)
from gn_module_monitoring.command.imports.sql import (
    check_rows_exist_in_import_table,
    create_sql_import_table_protocol,
)
from gn_module_monitoring.command.imports.utils import ask_confirmation
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
    monitoring_module_config_path,
    validate_json_file,
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

    # suppression source pour la synthese
    try:
        print("Remove source {}".format("MONITORING_" + module_code.upper()))
        source = get_source_by_code("MONITORING_" + module_code.upper())
        DB.session.delete(source)
        DB.session.commit()
    except Exception as e:
        print("Impossible de supprimer la source {}".format(str(e)))
        # return
    # run specific sql TODO
    # remove nomenclature TODO
    return


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


def validate_json_file_protocol(module_code: str):
    errors = []
    module_config_dir = Path(monitoring_module_config_path(module_code))
    config_path = module_config_dir / "config.json"
    valid_type_widgets = set(TYPE_WIDGET.keys())
    errors.extend(validate_json_file(config_path, valid_type_widgets))

    try:
        entities = get_entities_protocol(module_code)
        for entity_code in entities:
            if not entity_code == "sites_group":
                # Valid specific file
                specific_path = module_config_dir / f"{entity_code}.json"
                errors.extend(validate_json_file(specific_path, valid_type_widgets))

                # Valid generic file
                project_root = Path(__file__).parent.parent
                generic_path = project_root / "config" / "generic" / f"{entity_code}.json"
                errors.extend(validate_json_file(generic_path, valid_type_widgets))
    except Exception as e:
        errors.append(f"Erreur lors de la lecture des entités: {str(e)}")

    return len(errors) == 0, errors


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


def process_update_module_import(module_data, module_code: str):
    """
    Gère la mise à jour complète d'un module.
    """
    try:
        is_valid, messages, fields_to_delete, update_label_only = validate_protocol_changes(
            module_code, module_data
        )

        if is_valid is None:
            return None

        if not is_valid:
            print("Erreurs détectées lors de la validation du protocole:")
            for msg in messages:
                print(f"- {msg}")
            return False

        if messages:
            print("\nAvertissements concernant les modifications du protocole:")
            for msg in messages:
                print(f"- {msg}")

        if not ask_confirmation():
            return False
        else:
            return update_protocol(module_data, module_code, fields_to_delete, update_label_only)

    except Exception as e:
        print(f"Erreur lors du traitement du module {module_code}: {str(e)}")
        return False


def validate_protocol_changes(module_code: str, module_data):
    """
    Valide les changements dans les fichiers de configuration du protocole.

    Args:
        module_code: Code du module à valider.

    Returns:
        - Booléen indiquant si la validation a réussi.
        - Liste des messages d'erreur ou d'avertissement.
        - Champs à supprimer.
        - Booléen indiquant si seule la mise à jour du label est nécessaire.
    """
    try:
        destination = DB.session.execute(select(Destination).filter_by(code=module_code)).scalar()

        if check_rows_exist_in_import_table(module_code):
            return (
                False,
                [
                    "La table d'importation contient des données. Impossible de mettre à jour le protocole."
                ],
                [],
                False,
            )

        existing_data = get_existing_protocol_state(destination.id_destination, module_data)
        protocol_data, _ = get_protocol_data(module_code, destination.id_destination)

        all_new_fields = []
        for entity_fields in protocol_data.values():
            for field_type in ["generic", "specific"]:
                all_new_fields.extend(entity_fields[field_type])

        fields_to_add, fields_to_update, fields_to_delete = compare_protocol_fields(
            existing_data["fields"], all_new_fields
        )

        warnings = []
        if existing_data["label"]:
            warnings.append(
                f"INFO: Le libellé du module va être modifié. '{destination.label}' -> '{module_data['module'].get('module_label')}'"
            )

        if fields_to_delete:
            warnings.append(
                "ATTENTION: Des champs vont être supprimés. "
                f"Champs concernés: {', '.join(f['name_field'][3:] for f in fields_to_delete)}"
            )

        if fields_to_update:
            warnings.append(
                "ATTENTION: Des champs vont être modifiés. "
                f"Champs concernés: {', '.join(f['name_field'][3:] for f in fields_to_update)}"
            )

        if fields_to_add:
            warnings.append(
                "INFO: De nouveaux champs vont être ajoutés. "
                f"Champs concernés: {', '.join(f['name_field'][3:] for f in fields_to_add)}"
            )

        if (
            not fields_to_add
            and not fields_to_update
            and not fields_to_delete
            and existing_data["label"]
        ):
            return True, warnings, [], True

        if (
            not fields_to_add
            and not fields_to_update
            and not fields_to_delete
            and not existing_data["label"]
        ):
            warnings.append("Aucun changement détecté dans le protocole.")
            return None, warnings, [], False

        return True, warnings, fields_to_delete, False

    except Exception as e:
        return False, [f"Erreur lors de la validation du protocole: {str(e)}"], [], False
