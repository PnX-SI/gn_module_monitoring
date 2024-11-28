import os
import click
from pathlib import Path

from flask import current_app
from sqlalchemy import and_, text, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from geonature.utils.env import DB
from geonature.core.gn_permissions.models import (
    PermObject,
    PermissionAvailable,
    PermAction,
    cor_object_module,
)
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.imports.models import BibFields
from geonature.core.imports.models import Destination
from geonature.core.imports.models import Entity
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.config.utils import (
    json_from_file,
    monitoring_module_config_path,
    SUB_MODULE_CONFIG_DIR,
)

from gn_module_monitoring.config.repositories import get_config

from gn_module_monitoring.modules.repositories import get_module, get_source_by_code, get_modules


"""
utils.py

fonctions pour les commandes du module monitoring
"""


FORBIDDEN_SQL_INSTRUCTION = [
    "INSERT ",
    "DELETE ",
    "UPDATE ",
    "EXECUTE ",
    "TRUNCATE ",
    "ALTER ",
    "GRANT ",
    "COPY ",
    "PERFORM ",
    "CASCADE",
]

PERMISSION_LABEL = {
    "MONITORINGS_MODULES": {"label": "modules", "actions": ["R", "U", "E"]},
    "MONITORINGS_GRP_SITES": {"label": "groupes de sites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_SITES": {"label": "sites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_VISITES": {"label": "visites", "actions": ["C", "R", "U", "D"]},
}

ACTION_LABEL = {
    "C": "Créer des",
    "R": "Voir les",
    "U": "Modifier les",
    "D": "Supprimer des",
    "E": "Exporter les",
}


def process_sql_files(
    dir=None, module_code=None, depth=1, allowed_files=["export.sql", "synthese.sql"]
):
    sql_dir = Path(monitoring_module_config_path(module_code))
    if dir:
        sql_dir = sql_dir / "exports/csv"
    if not sql_dir.is_dir():
        return

    if not allowed_files:
        allowed_files = []
    count_depth = 0
    for root, dirs, files in os.walk(sql_dir, followlinks=True):
        count_depth = count_depth + 1
        for f in files:
            if not f.endswith(".sql"):
                continue
            if not f in allowed_files and allowed_files:
                continue
            # Vérification commandes non autorisée
            try:
                execute_sql_file(root, f, module_code, FORBIDDEN_SQL_INSTRUCTION)
                print("{} - exécution du fichier : {}".format(module_code, f))
            except Exception as e:
                print(e)

        # Limite profondeur de la recherche dans les répertoires
        if depth:
            if count_depth >= depth:
                break


def execute_sql_file(dir, file, module_code, forbidden_instruction=[]):
    """
    Execution d'un fichier sql dans la base de donnée
    dir : nom du répertoire
    file : nom du fichier à éxécuter
    module_code : code du module
    forbidden_instruction : liste d'instructions sql qui sont proscrites du fichier.

    """
    sql_content = Path(Path(dir) / file).read_text()
    for sql_cmd in forbidden_instruction:
        if sql_cmd.lower() in sql_content.lower():
            raise Exception(
                "erreur dans le script {} instruction sql non autorisée {}".format(
                    module_code, file, sql_cmd
                )
            )

    try:
        DB.engine.execute(
            text(sql_content),
            module_code=module_code,
        )
    except Exception as e:
        raise Exception("{} - erreur dans le script {} : {}".format(module_code, file, e))


def process_available_permissions(module_code, session):
    try:
        module = get_module("module_code", module_code)
    except Exception:
        print("le module n'existe pas")
        return

    config = get_config(module_code, force=True)
    if not config:
        print(f"Il y a un problème de configuration pour le module {module_code}")
        return

    tree = config.get("tree", [])

    module_objects = [k for k in extract_keys(tree, keys=[])]

    permission_level = current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})

    # Insert permission object
    for permission_object_code in module_objects:
        print(f"Création des permissions pour {module_code} : {permission_object_code}")
        insert_module_available_permissions(
            module_code, permission_level[permission_object_code], session=session
        )


def insert_module_available_permissions(module_code, perm_object_code, session):
    object_label = PERMISSION_LABEL.get(perm_object_code)["label"]

    if not object_label:
        print(f"L'object {perm_object_code} n'est pas traité")

    try:
        module = session.scalars(select(TModules).where(TModules.module_code == module_code)).one()
    except NoResultFound:
        print(f"Le module {module_code} n'est pas présent")
        return

    try:
        perm_object = session.execute(
            select(PermObject).where(PermObject.code_object == perm_object_code)
        ).scalar_one_or_none()
    except NoResultFound:
        print(f"L'object de permission {perm_object_code} n'est pas présent")
        return

    stmt = (
        pg_insert(cor_object_module)
        .values(id_module=module.id_module, id_object=perm_object.id_object)
        .on_conflict_do_nothing()
    )
    session.execute(stmt)
    session.commit()

    # Création d'une permission disponible pour chaque action
    object_actions = PERMISSION_LABEL.get(perm_object_code)["actions"]
    for action in object_actions:
        permaction = session.execute(
            select(PermAction).where(PermAction.code_action == action)
        ).scalar_one()
        try:
            perm = session.execute(
                select(PermissionAvailable).where(
                    PermissionAvailable.module == module,
                    PermissionAvailable.object == perm_object,
                    PermissionAvailable.action == permaction,
                )
            ).scalar_one()
        except NoResultFound:
            label = f"{ACTION_LABEL[action]} {object_label}"
            if action == "E" and perm_object.code_object == "MONITORINGS_MODULES":
                label = "Export les données du module"
            perm = PermissionAvailable(
                module=module,
                object=perm_object,
                action=permaction,
                label=label,
                scope_filter=True,
            )
            session.add(perm)


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

        stmt = delete(Destination).where(Destination.code == module_code)
        DB.session.execute(stmt)

        stmt = delete(TModules).where(TModules.id_module == module.id_module)
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


def add_nomenclature(module_code):
    path_nomenclature = monitoring_module_config_path(module_code) / "nomenclature.json"

    if not path_nomenclature.is_file():
        print("Il n'y a pas de nomenclature à insérer pour ce module")
        return

    nomenclature = json_from_file(path_nomenclature, None)
    if not nomenclature:
        print("Il y a un problème avec le fichier {}".format(path_nomenclature))
        return

    for data in nomenclature.get("types", []):
        nomenclature_type = DB.session.execute(
            select(BibNomenclaturesTypes).where(
                data.get("mnemonique") == BibNomenclaturesTypes.mnemonique
            )
        ).scalar_one_or_none()

        if nomenclature_type:
            action = "already exist"
            print(
                "nomenclature type {} - {} - {}".format(
                    nomenclature_type.mnemonique, nomenclature_type.label_default, action
                )
            )

            continue

        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"

        nomenclature_type = BibNomenclaturesTypes(**data)
        DB.session.add(nomenclature_type)
        DB.session.commit()
        action = "added"
        print(
            "nomenclature type {} - {} - {}".format(
                nomenclature_type.mnemonique, nomenclature_type.label_default, action
            )
        )

    for data in nomenclature["nomenclatures"]:
        insert_update_nomenclature(data)


def insert_update_nomenclature(data):

    # Get Id type
    id_type = DB.session.execute(
        select(BibNomenclaturesTypes.id_type).where(
            BibNomenclaturesTypes.mnemonique == data["type"]
        )
    ).scalar_one_or_none()

    if not id_type:
        print(
            'probleme de type avec mnemonique="{}" pour la nomenclature {}'.format(
                data["type"], data
            )
        )
        return

    # Get nomenclature if exist
    action = "updated"
    nomenclature = DB.session.execute(
        select(TNomenclatures)
        .join(BibNomenclaturesTypes, BibNomenclaturesTypes.id_type == TNomenclatures.id_type)
        .where(
            and_(
                data.get("cd_nomenclature") == TNomenclatures.cd_nomenclature,
                data.get("type") == BibNomenclaturesTypes.mnemonique,
            )
        )
    ).scalar_one_or_none()

    # If not create new one
    if not nomenclature:
        nomenclature = TNomenclatures()
        action = "added"

    data["label_fr"] = data.get("label_fr") or data["label_default"]
    data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
    data["source"] = data.get("source") or "monitoring"
    data["statut"] = data.get("statut") or "Validation en cours"
    data["active"] = True
    data["id_type"] = id_type

    for key, value in data.items():
        if hasattr(nomenclature, key):
            setattr(nomenclature, key, value)

    DB.session.add(nomenclature)
    DB.session.commit()
    if data["type"] == "TYPE_SITE":
        existing_bib_type_site = DB.session.get(BibTypeSite, nomenclature.id_nomenclature)
        if not existing_bib_type_site:
            bib_type_site = BibTypeSite(id_nomenclature_type_site=nomenclature.id_nomenclature)
            DB.session.add(bib_type_site)
            DB.session.commit()

    print(
        "nomenclature {} - {} - {}".format(
            nomenclature.cd_nomenclature, nomenclature.label_default, action
        )
    )


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
    FOnction permettant d'extraire de façon récursive les clés d'un dictionnaire
    """
    for key, val in test_dict.items():
        keys.append(key)
        if isinstance(val, dict):
            extract_keys(val, keys)
    return keys


def insert_bib_field(module_code, id_destination):
    TABLE_NAME = {
        "visit": "t_base_visits",
        "site": "t_base_sites",
        "observation": "t_observations",
        "sites_group": "t_sites_groups",
    }

    # Récupération des entités du module
    files = get_entities_module(module_code)
    module_config_dir_path = monitoring_module_config_path(module_code)

    label_entity = json_from_file(monitoring_module_config_path(module_code) / "site.json")
    if not label_entity:
        raise Exception(f"Le fichier site.json est absent")

    try:
        for file in files:
            file_path = module_config_dir_path / f"{file}.json"

            if not file_path.is_file():
                raise Exception(f"Le fichier {file}.json est manquant")

            data = json_from_file(file_path)
            if not data:
                raise Exception(f"Le fichier {file}.json est vide")

            generic_data = json_from_file(
                os.path.join(
                    os.path.dirname(__file__),
                    "gn_module_monitoring",
                    "backend",
                    "gn_module_monitoring",
                    "config",
                    "generic",
                    f"{file}.json",
                ),
                result_default={},
            )

            if not generic_data:
                raise Exception(f"Le fichier generic/{file}.json est vide")

            specific_fields = data.get("specific", {})
            generic_fields = generic_data.get("generic", {})

            merged_fields = []

            # Insérer le champ uuid_field_name en premier
            uuid_field_name = generic_data.get("uuid_field_name")
            if not uuid_field_name:
                raise Exception(f"`uuid_field_name` est absent dans {file}.json")

            uuid_field = {
                "name_field": uuid_field_name,
                "fr_label": uuid_field_name,
                "eng_label": None,
                "type_field": "uuid",
                "mandatory": False,
                "autogenerated": True,
                "display": True,
                "mnemonique": None,
                "source_field": None,
                "dest_field": uuid_field_name,
                "multi": False,
                "id_destination": id_destination,
                "mandatory_conditions": None,
                "optional_conditions": None,
            }
            merged_fields.append(uuid_field)

            # Champs communs avec surcouche
            common_fields = set(generic_fields.keys()).intersection(specific_fields.keys())
            for field_name in common_fields:
                field_data = generic_fields[field_name].copy()
                field_data.update(specific_fields[field_name])
                bib_field = {
                    "name_field": field_name,
                    "fr_label": field_data.get("attribut_label", ""),
                    "eng_label": None,
                    "type_field": field_data.get("type_widget", ""),
                    "mandatory": field_data.get("required", False),
                    "autogenerated": False,
                    "display": not field_data.get("hidden", False),
                    "mnemonique": None,
                    "source_field": None,
                    "dest_field": field_name,
                    "multi": False,
                    "id_destination": id_destination,
                    "mandatory_conditions": None,
                    "optional_conditions": None,
                }
                merged_fields.append(bib_field)

            # Champs additionnels spécifiques
            additional_fields = set(specific_fields.keys()).difference(generic_fields.keys())
            for field_name in additional_fields:
                field_data = specific_fields[field_name]
                bib_field = {
                    "name_field": field_name,
                    "fr_label": field_data.get("attribut_label", ""),
                    "eng_label": None,
                    "type_field": field_data.get("type_widget", ""),
                    "mandatory": field_data.get("required", False),
                    "autogenerated": False,
                    "display": not field_data.get("hidden", False),
                    "mnemonique": None,
                    "source_field": None,
                    "dest_field": field_name,
                    "multi": False,
                    "id_destination": id_destination,
                    "mandatory_conditions": None,
                    "optional_conditions": None,
                }
                merged_fields.append(bib_field)

            # Insérer les champs dans bib_fields
            inserted_fields = []
            for field in merged_fields:
                bib_field = BibFields(**field)
                DB.session.add(bib_field)
                inserted_fields.append(bib_field)

            # Commit temporaire pour `bib_fields`
            DB.session.flush()

            # Récupérer id_field pour uuid_field_name
            uuid_field = next(
                (f for f in inserted_fields if f.name_field == uuid_field_name), None
            )
            if not uuid_field:
                raise Exception(f"Le champ uuid_field_name n'a pas été inséré pour {file}.json")

            table_name = TABLE_NAME.get(file)
            label_en = label_entity.get("label")

            # Insérer dans bib_entities
            entity = Entity(
                id_destination=id_destination,
                code=file,
                label=label_en,
                order=None,
                validity_column=f"{file.lower()}_valid",
                destination_table_schema="gn_monitoring",
                destination_table_name=table_name,
                id_unique_column=uuid_field.id_field,
            )
            DB.session.add(entity)

        DB.session.commit()

    except Exception as e:
        DB.session.rollback()
        click.echo(f"Erreur lors de l'insertion : {str(e)}", err=True)

    finally:
        DB.session.close()


def valid_submodule_name(submodule_name):
    return submodule_name.replace("-", "_").lower()


def insert_bib_destinations(module_data):
    # Vérifier si le module parent MONITORINGS existe
    module_monitoring_code = DB.session.query(TModules).filter_by(module_code="MONITORINGS").one()

    protocol = valid_submodule_name(module_data["module_code"])

    # Vérifier l'existence dans bib_destinations
    existing_destination = (
        DB.session.query(Destination).filter_by(code=module_data["module_code"]).one_or_none()
    )

    if existing_destination:
        raise Exception(
            f"Le sous-module {module_data['module_code']} existe déjà dans bib_destinations"
        )

    submodule_data = {
        "id_module": module_monitoring_code.id_module,
        "code": module_data["module_code"],
        "label": module_data["module_label"],
        "table_name": f"t_import_{protocol}",
    }

    try:
        destination = Destination()
        destination.from_dict(submodule_data)
        DB.session.add(destination)
        DB.session.commit()
        return destination
    except Exception as e:
        DB.session.rollback()
        raise e


def get_entities_module(module_code):

    module_path = monitoring_module_config_path(module_code)

    if not (module_path / "config.json").is_file():
        raise Exception(f"Le fichier config.json est manquant pour le module {module_code}")

    data_config = json_from_file(module_path / "config.json")
    tree = data_config.get("tree", {}).get("module", {})
    keys = extract_keys(tree)
    unique_keys = list(dict.fromkeys(keys))

    return unique_keys
