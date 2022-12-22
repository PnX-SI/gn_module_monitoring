import pytest

from gn_module_monitoring.tests.fixtures.module import monitoring_module
from gn_module_monitoring.tests.fixtures.site import categories


@pytest.mark.usefixtures("temporary_transaction")
class TestModule:
    def test_module(self, monitoring_module):
        cateogories = monitoring_module.categories
        assert False
