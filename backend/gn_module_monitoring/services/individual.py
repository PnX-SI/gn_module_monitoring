from gn_module_monitoring.monitoring.models import TMonitoringIndividuals
from gn_module_monitoring.monitoring.schemas import MonitoringIndividualsSchema
from gn_module_monitoring.config.entities.individual import IndividualConfigSchema
from .base import BaseService


class IndividualService(BaseService):
    name = "individual"
    model = TMonitoringIndividuals
    model_schema = MonitoringIndividualsSchema
    config_schema = IndividualConfigSchema
