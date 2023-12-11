import os
from pathlib import Path

from flask import current_app
from sqlalchemy import and_, text, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import select
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.dialects.postgresql import insert as pg_insert

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_permissions.models import (
    PermObject,
    PermissionAvailable,
    PermAction,
    cor_object_module,
)
from geonature.core.gn_commons.models import TModules

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..config.utils import json_from_file, monitoring_module_config_path, SUB_MODULE_CONFIG_DIR

from ..config.repositories import get_config

from ..modules.repositories import get_module, get_source_by_code, get_modules


"""
utils.py

fonctions pour les commandes du module monitoring
"""


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


def process_for_all_module(process_func):
    """
    boucle sur les répertoire des module
        et exécute la fonction <process_func> pour chacun
        (sauf generic)
    """
    for module in get_modules():
        process_func(module.module_code)
    return


def process_export_csv(module_code=None):
    """
    fonction qui va chercher les fichier sql de exports/csv et qui les joue
    """

    if not module_code:
        """
        pour tous les modules
        """
        return process_for_all_module(process_export_csv)

    export_csv_dir = Path(monitoring_module_config_path(module_code)) / "exports/csv"

    if not export_csv_dir.is_dir():
        return

    for root, dirs, files in os.walk(export_csv_dir, followlinks=True):
        for f in files:
            if not f.endswith(".sql"):
                continue
            txt = Path(Path(root) / Path(f)).read_text()
            try:
                DB.session.execute(text(txt).bindparams(module_code=module_code))
                DB.session.commit()
                print("{} - export csv file : {}".format(module_code, f))

            except Exception as e:
                print("{} - export csv erreur dans le script {} : {}".format(module_code, f, e))


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
                select(PermissionAvailable)
                .where(PermissionAvailable.module == module)
                .where(PermissionAvailable.object == perm_object)
                .where(PermissionAvailable.action == permaction)
            ).scalar_one()
        except NoResultFound:
            perm = PermissionAvailable(
                module=module,
                object=perm_object,
                action=permaction,
                label=f"{ACTION_LABEL[action]} {object_label}",
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
        nomenclature_type = None
        try:
            nomenclature_type = DB.session.execute(
                select(BibNomenclaturesTypes).where(
                    data.get("mnemonique") == BibNomenclaturesTypes.mnemonique
                )
            ).scalar_one()

        except Exception:
            pass

        if nomenclature_type:
            print("no insert type", nomenclature_type)
            continue

        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"

        nomenclature_type = BibNomenclaturesTypes(**data)
        DB.session.add(nomenclature_type)
        DB.session.commit()

    for data in nomenclature["nomenclatures"]:
        nomenclature = None
        try:
            nomenclature = DB.session.execute(
                select(TNomenclatures)
                .join(
                    BibNomenclaturesTypes, BibNomenclaturesTypes.id_type == TNomenclatures.id_type
                )
                .where(
                    and_(
                        data.get("cd_nomenclature") == TNomenclatures.cd_nomenclature,
                        data.get("type") == BibNomenclaturesTypes.mnemonique,
                    )
                )
            ).scalar_one()

        except Exception as e:
            pass

        if nomenclature:
            # TODO make update
            print(
                "nomenclature {} - {} already exist".format(
                    nomenclature.cd_nomenclature, nomenclature.label_default
                )
            )
            continue

        id_type = None
        try:
            id_type = DB.session.execute(
                select(BibNomenclaturesTypes.id_type).where(
                    BibNomenclaturesTypes.mnemonique == data["type"]
                )
            ).scalar_one()
        except Exception as e:
            pass

        if not id_type:
            print(
                'probleme de type avec mnemonique="{}" pour la nomenclature {}'.format(
                    data["type"], data
                )
            )
            continue

        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"
        data["active"] = True
        data["id_type"] = id_type
        data.pop("type")

        nomenclature = TNomenclatures(**data)
        DB.session.add(nomenclature)
        DB.session.commit()
        print(
            "nomenclature {} - {} added".format(
                nomenclature.cd_nomenclature, nomenclature.label_default
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
