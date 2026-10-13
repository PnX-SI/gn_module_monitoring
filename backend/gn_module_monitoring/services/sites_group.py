from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema

from gn_module_monitoring.config.entities.sites_group import SitesGroupConfigSchema


class SitesGroupService:
    model = TMonitoringSitesGroups
    model_schema = MonitoringSitesGroupsSchema
    config_schema = SitesGroupConfigSchema
