from gn_module_monitoring.monitoring.models import TMonitoringMarkingEvent
from gn_module_monitoring.monitoring.schemas import MonitoringMarkingSchemaCruved

from gn_module_monitoring.config.entities.marking import MarkingEntityConfigSchema
from gn_module_monitoring.monitoring.import_actions.marking_actions import MarkingImportActions
from .base import BaseEntity


class MarkingEntity(BaseEntity):
    name = "marking"
    import_field_prefix = "m__"
    model = TMonitoringMarkingEvent
    model_schema_class = MonitoringMarkingSchemaCruved
    config_schema_class = MarkingEntityConfigSchema
    import_actions_class = MarkingImportActions
