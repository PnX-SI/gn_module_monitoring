import os
from pathlib import Path
from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_permissions.models import PermObject
from geonature.core.gn_commons.models import TModules

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..config.utils import json_from_file, monitoring_module_config_path, SUB_MODULE_CONFIG_DIR

from ..config.repositories import get_config

from ..modules.repositories import get_module, get_source_by_code, get_modules

"""
utils.py

fonctions pour les commandes du module monitoring
"""


def process_for_all_module(process_func):
    """
    boucle sur les répertoire des module
        et exécute la fonction <process_func> pour chacun
        (sauf generic)
    """
    for module in get_modules():
        process_func(module.module_code)
    return


def getMonitoringPermissionObjectLabel_dict():
    return __import__(
        "gn_module_monitoring"
    ).monitoring.definitions.MonitoringPermissionObjectLabel_dict


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


def process_available_permissions(module_code):
    try:
        module = get_module("module_code", module_code)
    except Exception:
        print("le module n'existe pas")
        return

    config = get_config(module_code, force=True)
    if not config:
        print(f"Il y a un problème de configuration pour le module {module_code}")
        return

    insert_module_available_permissions(module_code, "ALL")

    # Insert permission object
    for permission_object_code in config.get("permission_objects", []):
        insert_module_available_permissions(module_code, permission_object_code)


def insert_module_available_permissions(module_code, perm_object_code):
    print(
        f"process permissions for (module_code, perm_object)= ({module_code},{perm_object_code})"
    )

    object_label = getMonitoringPermissionObjectLabel_dict().get(perm_object_code)

    if not object_label:
        print(f"L'object {perm_object_code} n'est pas traité")

    try:
        module = TModules.query.filter_by(module_code=module_code).one()
    except NoResultFound:
        print("Le module {module_code} n'est pas présent")
        return

    try:
        perm_object = PermObject.query.filter_by(code_object=perm_object_code).one()
    except NoResultFound:
        print("L'object de permission {module_code} n'est pas présent")
        return

    txt_cor_object_module = f"""
        INSERT INTO gn_permissions.cor_object_module(
            id_module,
            id_object
        )
        VALUES({module.id_module}, {perm_object.id_object})
        ON CONFLICT DO NOTHING
    """
    DB.engine.execution_options(autocommit=True).execute(txt_cor_object_module)

    txt_perm_available = f"""
        INSERT INTO gn_permissions.t_permissions_available (
                id_module,
                id_object,
                id_action,
                label,
                scope_filter)
        SELECT
            {module.id_module},
            {perm_object.id_object},
            a.id_action,
            v.label,
            true
        FROM
            ( VALUES
                ('C', 'Créer des {object_label}'),
                ('R', 'Voir les {object_label}'),
                ('U', 'Modifier les {object_label}'),
                ('D', 'Supprimer des {object_label}'),
                ('E', 'Exporter les {object_label}')
            ) AS v (action_code, label)
        JOIN gn_permissions.bib_actions a ON v.action_code = a.code_action
        ON CONFLICT DO NOTHING
        """
    DB.engine.execution_options(autocommit=True).execute(txt_perm_available)


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


def installed_modules():
    return [
        {
            "module_code": module.module_code,
            "module_label": module.module_label,
            "module_desc": module.module_desc,
        }
        for module in get_modules()
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
