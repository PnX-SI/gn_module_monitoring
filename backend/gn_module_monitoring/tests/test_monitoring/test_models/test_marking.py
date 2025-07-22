import pytest

from geonature.core.gn_monitoring.models import TMarkingEvent
from gn_module_monitoring.monitoring.models import (
    PermissionModel,
    TMonitoringMarkingEvent,
    MonitoringQuery,
)


class TestMonitoringMarkingEvent:
    def test_model_inheritance(self):
        assert issubclass(TMonitoringMarkingEvent, TMarkingEvent)
        assert issubclass(TMonitoringMarkingEvent, PermissionModel)
        assert issubclass(TMonitoringMarkingEvent, MonitoringQuery)
