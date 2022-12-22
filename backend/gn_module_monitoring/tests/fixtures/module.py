from uuid import uuid4

import pytest
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.tests.fixtures.site import categories


@pytest.fixture
def monitoring_module(categories):
    t_monitoring_module = TMonitoringModules(
        module_code=uuid4(),
        module_label="test",
        active_frontend=True,
        active_backend=False,
        module_path="test",
        categories=list(categories.values()),
    )

    with db.session.begin_nested():
        db.session.add(t_monitoring_module)

    return t_monitoring_module
