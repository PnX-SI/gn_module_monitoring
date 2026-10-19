from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema

from gn_module_monitoring.config.entities.sites_group import SitesGroupEntityConfigSchema
from .base import BaseEntity


class SitesGroupEntity(BaseEntity):
    name = "sites_group"
    model = TMonitoringSitesGroups
    model_schema_class = MonitoringSitesGroupsSchema
    config_schema_class = SitesGroupEntityConfigSchema
