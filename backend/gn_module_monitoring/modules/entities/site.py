from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import MonitoringSitesSchema

from gn_module_monitoring.config.entities.site import SiteEntityConfigSchema
from .base import BaseEntity


class SiteEntity(BaseEntity):
    name = "site"
    model = TMonitoringSites
    model_schema_class = MonitoringSitesSchema
    config_schema_class = SiteEntityConfigSchema
