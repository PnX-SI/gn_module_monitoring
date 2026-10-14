from gn_module_monitoring.monitoring.models import TMonitoringVisits
from gn_module_monitoring.monitoring.schemas import MonitoringVisitsSchema

from gn_module_monitoring.config.entities.visit import VisitConfigSchema
from .base import BaseService


class VisitService(BaseService):
    name = "visit"
    model = TMonitoringVisits
    model_schema = MonitoringVisitsSchema
    config_schema = VisitConfigSchema
