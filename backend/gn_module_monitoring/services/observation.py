from gn_module_monitoring.monitoring.models import TMonitoringObservations
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsSchema

from gn_module_monitoring.config.entities.observation import ObservationConfigSchema
from .base import BaseService


class ObservationService(BaseService):
    name = "observation"
    model = TMonitoringObservations
    model_schema = MonitoringObservationsSchema
    config_schema = ObservationConfigSchema
