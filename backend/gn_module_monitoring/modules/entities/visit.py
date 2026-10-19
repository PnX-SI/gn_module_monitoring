from gn_module_monitoring.monitoring.models import TMonitoringVisits
from gn_module_monitoring.monitoring.schemas import MonitoringVisitsSchema

from gn_module_monitoring.config.entities.visit import VisitEntityConfigSchema
from .base import BaseEntity


class VisitEntity(BaseEntity):
    name = "visit"
    model = TMonitoringVisits
    model_schema_class = MonitoringVisitsSchema
    config_schema_class = VisitEntityConfigSchema
