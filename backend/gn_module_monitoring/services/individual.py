from gn_module_monitoring.monitoring.models import TMonitoringIndividuals
from gn_module_monitoring.monitoring.schemas import MonitoringIndividualsSchema
from gn_module_monitoring.config.entities.individual import IndividualConfigSchema


class IndividualService:
    model = TMonitoringIndividuals
    model_schema = MonitoringIndividualsSchema
    config_schema = IndividualConfigSchema
