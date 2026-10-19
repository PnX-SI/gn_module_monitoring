from gn_module_monitoring.monitoring.models import TMonitoringIndividuals
from gn_module_monitoring.monitoring.schemas import MonitoringIndividualsSchema
from gn_module_monitoring.config.entities.individual import IndividualEntityConfigSchema
from .base import BaseEntity


class IndividualEntity(BaseEntity):
    name = "individual"
    model = TMonitoringIndividuals
    model_schema_class = MonitoringIndividualsSchema
    config_schema_class = IndividualEntityConfigSchema
