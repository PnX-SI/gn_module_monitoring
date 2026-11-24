from gn_module_monitoring.monitoring.models import TMonitoringVisits
from gn_module_monitoring.monitoring.schemas import MonitoringVisitsSchemaCruved

from gn_module_monitoring.config.entities.visit import VisitEntityConfigSchema
from gn_module_monitoring.monitoring.import_actions.visit_actions import VisitImportActions
from .base import BaseEntity


class VisitEntity(BaseEntity):
    name = "visit"
    import_field_prefix = "v__"
    model = TMonitoringVisits
    model_schema_class = MonitoringVisitsSchemaCruved
    config_schema_class = VisitEntityConfigSchema
    import_actions_class = VisitImportActions
