from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.monitoring.schemas import MonitoringModuleSchema

from gn_module_monitoring.config.entities.module import ModuleConfigSchema


class ModuleService:
    model = TMonitoringModules
    model_schema = MonitoringModuleSchema
    config_schema = ModuleConfigSchema
