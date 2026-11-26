from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchemaCruved

from gn_module_monitoring.config.entities.sites_group import SitesGroupEntityConfigSchema
from gn_module_monitoring.monitoring.import_actions.sites_group_actions import (
    SitesGroupImportActions,
)
from .base import BaseEntity


class SitesGroupEntity(BaseEntity):
    name = "sites_group"
    model = TMonitoringSitesGroups
    model_schema_class = MonitoringSitesGroupsSchemaCruved
    config_schema_class = SitesGroupEntityConfigSchema
    import_actions_class = SitesGroupImportActions
