from uuid import uuid4

import pytest
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringModules


from geonature.core.gn_permissions.models import (
    PermFilterType,
    PermAction,
    PermObject,
    Permission,
)
from geonature.core.gn_commons.models import TModules, TMedias, BibTablesLocation
from pypnusershub.db.models import (
    User,
    Organisme,
    Application,
    Profils as Profil,
    UserApplicationRight,
)
from .generic import monitorings_users
import pytest
import shutil

from pathlib import Path
from flask import current_app

from gn_module_monitoring.command.cmd import (
    cmd_install_monitoring_module,
    cmd_remove_monitoring_module_cmd,
)
from gn_module_monitoring.monitoring.models import TMonitoringModules
from geonature.utils.env import BACKEND_DIR, DB


@pytest.fixture
def install_module_test():
    # Copy des fichiers du module de test
    path_gn_monitoring = Path(__file__).absolute().parent.parent.parent.parent.parent
    path_module_test = path_gn_monitoring / Path("contrib/test")
    path_gn_monitoring = BACKEND_DIR / Path("media/monitorings/test")
    shutil.copytree(path_module_test, path_gn_monitoring, dirs_exist_ok=True)

    # Installation du module
    runner = current_app.test_cli_runner()
    result = runner.invoke(cmd_install_monitoring_module, ["test"])


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
        actions = {code: PermAction.query.filter_by(code_action=code).one() for code in "CRUVED"}
        type_code_object = [
            "MONITORINGS_MODULES",
            "MONITORINGS_GRP_SITES",
            "MONITORINGS_SITES",
            "MONITORINGS_VISITES",
        ]
        for co in type_code_object:
            object_all = PermObject.query.filter_by(code_object=co).one()
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
