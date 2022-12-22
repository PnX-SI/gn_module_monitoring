import pytest
from geonature.core.gn_commons.models.base import TModules
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.tests.fixtures.site import categories


@pytest.fixture
def monitoring_module(module, categories):
    id_module = TModules.query.filter(TModules.id_module == module.id_module).one().id_module
    t_monitoring_module = TMonitoringModules()

    module_data = {"id_module": id_module, "categories": list(categories.values())}
    t_monitoring_module.from_dict(module_data)
    # monitoring = TMonitoringModules(id_module=id_module, categories=list(categories.values()))
    monitoring = t_monitoring_module
    with db.session.begin_nested():
        db.session.add(monitoring)

    return monitoring
