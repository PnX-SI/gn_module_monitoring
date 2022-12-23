import pytest
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringModules


@pytest.mark.usefixtures("temporary_transaction")
class TestModule:
    def test_module(self, monitoring_module, categories):
        cats = monitoring_module.categories
        assert cats == list(categories.values())

    def test_remove_categorie_from_module(self, monitoring_module, categories):
        with db.session.begin_nested():
            monitoring_module.categories.pop(0)

        mon = TMonitoringModules.query.filter_by(id_module=monitoring_module.id_module).one()

        assert len(mon.categories) == len(categories) - 1
