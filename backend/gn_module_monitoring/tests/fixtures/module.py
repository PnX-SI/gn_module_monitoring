import pytest
import pytest
import shutil

from uuid import uuid4
from pathlib import Path
from flask import current_app

from sqlalchemy import select

from geonature.utils.env import db, BACKEND_DIR
from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)

from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.command.cmd import (
    cmd_install_monitoring_module,
)
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.tests.fixtures.generic import monitorings_users
from gn_module_monitoring.tests.fixtures.type_site import types_site


@pytest.fixture
def install_module_test(types_site):
    # Copy des fichiers du module de test
    path_gn_monitoring = Path(__file__).absolute().parent.parent.parent.parent.parent
    path_module_test = path_gn_monitoring / Path("contrib/test")
    path_gn_monitoring = BACKEND_DIR / Path("media/monitorings/test")
    shutil.copytree(src=str(path_module_test), dst=str(path_gn_monitoring), dirs_exist_ok=True)

    # Installation du module
    runner = current_app.test_cli_runner()
    result = runner.invoke(cmd_install_monitoring_module, ["test"])

    assert result.exit_code == 0
    # Association du module aux types de site existant
    module = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one()
    with db.session.begin_nested():
        module.types_site = list(types_site.values())
        db.session.add(module)


@pytest.fixture
def monitoring_module(types_site, monitorings_users):
    t_monitoring_module = TMonitoringModules(
        module_code="TEST",
        uuid_module_complement=uuid4(),
        module_label="test",
        active_frontend=True,
        active_backend=False,
        b_synthese=False,
        module_path="test",
        types_site=list(types_site.values()),
    )

    with db.session.begin_nested():
        db.session.add(t_monitoring_module)
        # Set module Permission

        actions = {
            code: db.session.execute(
                select(PermAction).where(PermAction.code_action == code)
            ).scalar_one()
            for code in "CRUVED"
        }

        type_code_object = [
            "MONITORINGS_MODULES",
            "MONITORINGS_GRP_SITES",
            "MONITORINGS_SITES",
            "MONITORINGS_VISITES",
        ]
        for co in type_code_object:
            object_all = db.session.execute(
                select(PermObject).where(PermObject.code_object == co)
            ).scalar_one()

            for action in actions.values():
                for obj in [object_all] + t_monitoring_module.objects:
                    permission = Permission(
                        role=monitorings_users["admin_user"],
                        action=action,
                        module=t_monitoring_module,
                        object=obj,
                        scope_value=None,
                        sensitivity_filter=None,
                    )
                    db.session.add(permission)

    return t_monitoring_module


@pytest.fixture
def monitoring_module_wo_types_site():
    t_monitoring_module = TMonitoringModules(
        module_code=uuid4(),
        module_label="NoType",
        active_frontend=True,
        active_backend=False,
        module_path="NoType",
        b_synthese=False,
    )

    with db.session.begin_nested():
        db.session.add(t_monitoring_module)

    return t_monitoring_module


@pytest.fixture
def modules_with_and_without_permission(types_site, monitorings_users):
    user = monitorings_users["admin_user"]

    module_with_perm = TMonitoringModules(
        module_code="WITH_PERM",
        module_label="Module With Perm",
        uuid_module_complement=uuid4(),
        module_path="with_perm",
        active_frontend=True,
        active_backend=False,
        types_site=list(types_site.values()),
    )

    module_without_perm = TMonitoringModules(
        module_code="NO_PERM",
        module_label="Module Without Perm",
        uuid_module_complement=uuid4(),
        module_path="no_perm",
        active_frontend=True,
        active_backend=False,
        types_site=list(types_site.values()),
    )

    with db.session.begin_nested():
        db.session.add_all([module_with_perm, module_without_perm])

        action_r = db.session.execute(
            select(PermAction).where(PermAction.code_action == "R")
        ).scalar_one()

        # PermObjets
        objects = {
            code: db.session.execute(
                select(PermObject).where(PermObject.code_object == code)
            ).scalar_one()
            for code in [
                "MONITORINGS_MODULES",
                "MONITORINGS_GRP_SITES",
                "MONITORINGS_SITES",
                "MONITORINGS_VISITES",
            ]
        }

        # Ajout de droits complets sur tous les objets (y compris VISITES)
        for obj in objects.values():
            db.session.add(
                Permission(
                    role=user,
                    action=action_r,
                    module=module_with_perm,
                    object=obj,
                    scope_value=None,
                    sensitivity_filter=None,
                )
            )

        # Ajout de droits limités pour module_without_perm (pas MONITORINGS_VISITES)
        for code in ["MONITORINGS_MODULES", "MONITORINGS_GRP_SITES", "MONITORINGS_SITES"]:
            db.session.add(
                Permission(
                    role=user,
                    action=action_r,
                    module=module_without_perm,
                    object=objects[code],
                    scope_value=None,
                    sensitivity_filter=None,
                )
            )

    return {"with_perm": module_with_perm, "without_perm": module_without_perm}


@pytest.fixture
def modules_with_permissions_and_different_types(types_site, monitorings_users):
    admin_user = monitorings_users["admin_user"]
    modules = {}

    with db.session.begin_nested():
        action_r = db.session.execute(
            select(PermAction).where(PermAction.code_action == "R")
        ).scalar_one()
        perm_object = db.session.execute(
            select(PermObject).where(PermObject.code_object == "MONITORINGS_VISITES")
        ).scalar_one()

        for label, type_site in types_site.items():
            module = TMonitoringModules(
                module_code=f"MOD_{label}",
                module_label=f"Module {label}",
                module_path=f"path_{label}",
                uuid_module_complement=uuid4(),
                active_frontend=True,
                active_backend=True,
                types_site=[type_site],
            )
            db.session.add(module)

            # On donne la permission "R"
            permission = Permission(
                role=admin_user, action=action_r, module=module, object=perm_object
            )
            db.session.add(permission)

            modules[label] = module

    return {"admin_user": admin_user, "modules": modules}
