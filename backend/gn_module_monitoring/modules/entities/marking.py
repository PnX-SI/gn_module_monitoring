from gn_module_monitoring.monitoring.models import TMonitoringMarkingEvent
from gn_module_monitoring.monitoring.schemas import MonitoringMarkingSchema

from gn_module_monitoring.config.entities.marking import MarkingEntityConfigSchema
from .base import BaseEntity


class MarkingEntity(BaseEntity):
    name = "marking"
    model = TMonitoringMarkingEvent
    model_schema_class = MonitoringMarkingSchema
    config_schema_class = MarkingEntityConfigSchema
