from gn_module_monitoring.monitoring.models import TMonitoringObservationDetails
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsDetailsSchemaCruved

from gn_module_monitoring.config.entities.observation_detail import (
    ObservationDetailEntityConfigSchema,
)
from gn_module_monitoring.monitoring.import_actions.observation_detail_actions import (
    ObservationDetailImportActions,
)
from .base import BaseEntity


class ObservationDetailEntity(BaseEntity):
    name = "observation_detail"
    model = TMonitoringObservationDetails
    model_schema_class = MonitoringObservationsDetailsSchemaCruved
    config_schema_class = ObservationDetailEntityConfigSchema
    import_actions_class = ObservationDetailImportActions
