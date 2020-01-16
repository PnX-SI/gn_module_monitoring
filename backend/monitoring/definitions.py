from geonature.core.gn_commons.models import TMedias
from ..models.monitoring import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringObservationDetails,
)
from .objects import (
    MonitoringModule,
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
    'site': TMonitoringSites,
    'visit': TMonitoringVisits,
    'observation': TMonitoringObservations,
    'detail': TMonitoringObservationDetails,
    'media': TMedias,
}


MonitoringObjects_dict = {
    'module': MonitoringModule,
    'site': MonitoringSite,
    'visit': MonitoringVisit,
    'observation': MonitoringObject,
    'observation_detail': MonitoringObject,
    'media': MonitoringObject
}

monitoring_definitions.set(MonitoringObjects_dict, MonitoringModels_dict)
