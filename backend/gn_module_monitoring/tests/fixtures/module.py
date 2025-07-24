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
from gn_module_monitoring.tests.fixtures.generic import add_user_permission
from gn_module_monitoring.tests.fixtures.type_site import types_site


@pytest.fixture
def install_module_test(types_site, users):
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

    # Association des permissions aux différents utilisateurs
    users_to_create = [
        ("noright_user", 0),
        ("stranger_user", 2),
        ("associate_user", 2),
        ("self_user", 1),
        ("user", 2),
        ("admin_user", 3),
    ]

    type_code_object = [
        "MONITORINGS_MODULES",
        "MONITORINGS_GRP_SITES",
        "MONITORINGS_SITES",
        "MONITORINGS_VISITES",
        "MONITORINGS_INDIVIDUALS",
        "MONITORINGS_MARKINGS",
        "ALL",
    ]

    for username, scope in users_to_create:
        for code_object in type_code_object:
            add_user_permission(
                module.module_code,
                users[username],
                scope=scope,
                type_code_object=code_object,
                code_action="CRUVD",
            )

    # This is required because the first call to get_config during the install command cannot get the site types
    # (because the module does not exist yet in the DB) but this incomplete config is still registered with the cache.
    from gn_module_monitoring.config.repositories import get_config

    get_config("test", force=True)


@pytest.fixture
def monitoring_module(types_site, users):
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
                        role=users["admin_user"],
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
def modules_with_and_without_permission(types_site, users):
    user = users["admin_user"]

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

    # Ajout de droits complets sur tous les objets (y compris VISITES)
    for type_code_object in [
        "MONITORINGS_MODULES",
        "MONITORINGS_GRP_SITES",
        "MONITORINGS_SITES",
        "MONITORINGS_VISITES",
    ]:
        add_user_permission(
            module_with_perm.module_code, user, 3, type_code_object, code_action="R"
        )

        # Ajout de droits limités pour module_without_perm (pas MONITORINGS_VISITES)
    for type_code_object in ["MONITORINGS_MODULES", "MONITORINGS_GRP_SITES", "MONITORINGS_SITES"]:
        add_user_permission(
            module_without_perm.module_code, user, 3, type_code_object, code_action="R"
        )

    return {"with_perm": module_with_perm, "without_perm": module_without_perm}


@pytest.fixture
def modules_with_permissions_and_different_types(types_site, users):
    admin_user = users["admin_user"]
    modules = {}

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

        with db.session.begin_nested():
            db.session.add(module)
        add_user_permission(
            module.module_code, admin_user, 3, "MONITORINGS_VISITES", code_action="R"
        )

        modules[label] = module

    return {"admin_user": admin_user, "modules": modules}
