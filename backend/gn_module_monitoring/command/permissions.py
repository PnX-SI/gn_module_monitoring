from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert


from geonature.core.gn_permissions.models import (
    PermObject,
    PermissionAvailable,
    PermAction,
    cor_object_module,
)
from geonature.core.gn_commons.models import TModules


from gn_module_monitoring.command.imports.constant import ACTION_LABEL, PERMISSION_LABEL
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.utils.utils import extract_keys
from gn_module_monitoring.modules.repositories import get_module


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
