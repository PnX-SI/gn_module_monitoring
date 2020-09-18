from ..models.monitoring import (
    TMonitoringModules,
    TMonitoringSites_groups,
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringObservationDetails
)
from .objects import (
    MonitoringModule,
    MonitoringSites_group,
    MonitoringSite,
    MonitoringVisit
)
from .base import monitoring_definitions
from .repositories import MonitoringObject


'''
    MonitoringModels_dict :
    Fait le lien entre les monitoring_objects
    et les modèles sqlalchemy
'''

MonitoringModels_dict = {
    'module': TMonitoringModules,
    'sites_group': TMonitoringSites_groups,
    'site': TMonitoringSites,
    'visit': TMonitoringVisits,
    'observation': TMonitoringObservations,
    'detail': TMonitoringObservationDetails,
}


MonitoringObjects_dict = {
    'module': MonitoringModule,
    'sites_group': MonitoringSites_group,
    'site': MonitoringSite,
    'visit': MonitoringVisit,
    'observation': MonitoringObject,
    'observation_detail': MonitoringObject,
}

monitoring_definitions.set(MonitoringObjects_dict, MonitoringModels_dict)
