import os
from pathlib import Path

from flask import current_app
from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_permissions.models import PermObject, PermissionAvailable, PermAction
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

            try:
                DB.engine.execute(
                    text(open(Path(root) / f, "r").read())
                    .execution_options(autocommit=True)
                    .bindparams(module_code=module_code)
                )
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
        module = session.query(TModules).filter_by(module_code=module_code).one()
    except NoResultFound:
        print(f"Le module {module_code} n'est pas présent")
        return

    try:
        perm_object = session.query(PermObject).filter_by(code_object=perm_object_code).one()
    except NoResultFound:
        print(f"L'object de permission {perm_object_code} n'est pas présent")
        return

    txt_cor_object_module = f"""
        INSERT INTO gn_permissions.cor_object_module(
            id_module,
            id_object
        )
        VALUES({module.id_module}, {perm_object.id_object})
        ON CONFLICT DO NOTHING
    """
    session.execute(txt_cor_object_module)

    # Création d'une permission disponible pour chaque action
    object_actions = PERMISSION_LABEL.get(perm_object_code)["actions"]
    for action in object_actions:
        permaction = session.query(PermAction).filter_by(code_action=action).one()
        try:
            perm = (
                session.query(PermissionAvailable)
                .filter_by(module=module, object=perm_object, action=permaction)
                .one()
            )
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
        txt = f"DELETE FROM gn_permissions.t_permissions_available WHERE id_module = {module.id_module}"
        DB.engine.execution_options(autocommit=True).execute(txt)

        # HACK pour le moment suppresion avec un sql direct
        #  Car il y a un soucis de delete cascade dans les modèles sqlalchemy
        txt = f"""DELETE FROM gn_commons.t_modules WHERE id_module ={module.id_module}"""
        DB.engine.execution_options(autocommit=True).execute(txt)
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
            nomenclature_type = (
                DB.session.query(BibNomenclaturesTypes)
                .filter(data.get("mnemonique") == BibNomenclaturesTypes.mnemonique)
                .one()
            )

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
            nomenclature = (
                DB.session.query(TNomenclatures)
                .join(
                    BibNomenclaturesTypes, BibNomenclaturesTypes.id_type == TNomenclatures.id_type
                )
                .filter(
                    and_(
                        data.get("cd_nomenclature") == TNomenclatures.cd_nomenclature,
                        data.get("type") == BibNomenclaturesTypes.mnemonique,
                    )
                )
                .one()
            )

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
            id_type = (
                DB.session.query(BibNomenclaturesTypes.id_type)
                .filter(BibNomenclaturesTypes.mnemonique == data["type"])
                .one()
            )[0]
        except Exception:
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
