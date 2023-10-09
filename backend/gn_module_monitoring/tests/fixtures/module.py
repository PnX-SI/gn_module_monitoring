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


@pytest.fixture
def monitoring_module(types_site, monitorings_users):
    t_monitoring_module = TMonitoringModules(
        module_code="TEST",
        uuid_module_complement=uuid4(),
        module_label="test",
        active_frontend=True,
        active_backend=False,
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
    )

    with db.session.begin_nested():
        db.session.add(t_monitoring_module)

    return t_monitoring_module
