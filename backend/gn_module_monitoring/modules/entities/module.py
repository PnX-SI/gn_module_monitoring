from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.monitoring.schemas import MonitoringModuleSchema

from gn_module_monitoring.config.entities.module import ModuleEntityConfigSchema
from .base import BaseEntity


class ModuleEntity(BaseEntity):
    name = "module"
    model = TMonitoringModules
    model_schema_class = MonitoringModuleSchema
    config_schema_class = ModuleEntityConfigSchema
