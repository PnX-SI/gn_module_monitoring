from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.monitoring.schemas import MonitoringModuleSchema

from gn_module_monitoring.config.entities.module import ModuleConfigSchema
from .base import BaseService


class ModuleService(BaseService):
    name = "module"
    model = TMonitoringModules
    model_schema = MonitoringModuleSchema
    config_schema = ModuleConfigSchema
