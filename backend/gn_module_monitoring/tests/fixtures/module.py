from uuid import uuid4

import pytest
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringModules


@pytest.fixture
def monitoring_module(types_site):
    t_monitoring_module = TMonitoringModules(
        module_code=uuid4(),
        module_label="test",
        active_frontend=True,
        active_backend=False,
        module_path="test",
        types_site=list(types_site.values()),
    )

    with db.session.begin_nested():
        db.session.add(t_monitoring_module)

    return t_monitoring_module
