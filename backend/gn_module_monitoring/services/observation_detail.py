from gn_module_monitoring.monitoring.models import TMonitoringObservationDetails
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsDetailsSchema

from gn_module_monitoring.config.entities.observation_detail import ObservationDetailConfigSchema
from .base import BaseService


class ObservationDetailService(BaseService):
    name = "observation_detail"
    model = TMonitoringObservationDetails
    model_schema = MonitoringObservationsDetailsSchema
    config_schema = ObservationDetailConfigSchema
