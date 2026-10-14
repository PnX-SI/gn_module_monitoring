from gn_module_monitoring.monitoring.models import TMonitoringMarkingEvent
from gn_module_monitoring.monitoring.schemas import MonitoringMarkingSchema

from gn_module_monitoring.config.entities.marking import MarkingConfigSchema
from .base import BaseService


class MarkingService(BaseService):
    name = "marking"
    model = TMonitoringMarkingEvent
    model_schema = MonitoringMarkingSchema
    config_schema = MarkingConfigSchema
