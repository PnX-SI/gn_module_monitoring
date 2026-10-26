from gn_module_monitoring.monitoring.models import TMonitoringObservations
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsSchema

from gn_module_monitoring.config.entities.observation import ObservationEntityConfigSchema
from .base import BaseEntity


class ObservationEntity(BaseEntity):
    name = "observation"
    model = TMonitoringObservations
    model_schema_class = MonitoringObservationsSchema
    config_schema_class = ObservationEntityConfigSchema
