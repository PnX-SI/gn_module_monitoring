from gn_module_monitoring.monitoring.models import TMonitoringObservations
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsSchema

from gn_module_monitoring.config.entities.observation_detail import ObservationDetailConfigSchema


class ObservationDetailService:
    model = TMonitoringObservations
    model_schema = MonitoringObservationsSchema
    config_schema = ObservationDetailConfigSchema
