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


@pytest.fixture
def install_module_test():
    # Copy des fichiers du module de test
    path_gn_monitoring = Path(__file__).absolute().parent.parent.parent.parent.parent
    path_module_test = path_gn_monitoring / Path("contrib/test")
    path_gn_monitoring = BACKEND_DIR / Path("media/monitorings/test")
    print(str(path_module_test), str(path_gn_monitoring))
    shutil.copytree(src=str(path_module_test), dst=str(path_gn_monitoring), dirs_exist_ok=True)

    # Installation du module
    runner = current_app.test_cli_runner()
    result = runner.invoke(cmd_install_monitoring_module, ["test"])

    assert result.exit_code == 0


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
