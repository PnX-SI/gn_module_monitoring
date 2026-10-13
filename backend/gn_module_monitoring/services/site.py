from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import MonitoringSitesSchema

from gn_module_monitoring.config.entities.site import SiteConfigSchema


class SiteService:
    model = TMonitoringSites
    model_schema = MonitoringSitesSchema
    config_schema = SiteConfigSchema
