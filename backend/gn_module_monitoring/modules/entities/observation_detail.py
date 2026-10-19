from gn_module_monitoring.monitoring.models import TMonitoringObservationDetails
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsDetailsSchema

from gn_module_monitoring.config.entities.observation_detail import ObservationDetailEntityConfigSchema
from .base import BaseEntity


class ObservationDetailEntity(BaseEntity):
    name = "observation_detail"
    model = TMonitoringObservationDetails
    model_schema_class = MonitoringObservationsDetailsSchema
    config_schema_class = ObservationDetailEntityConfigSchema
