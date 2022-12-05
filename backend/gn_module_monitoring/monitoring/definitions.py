from .models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringObservationDetails,
    TMonitoringSitesGroups,
)
from .objects import (
    MonitoringModule,
    MonitoringSite
)

from .base import monitoring_definitions
from .repositories import MonitoringObject
from .geom import MonitoringObjectGeom


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
    'sites_group': TMonitoringSitesGroups
}

MonitoringObjects_dict = {
    'module': MonitoringModule,  # besoin pour retrouver le module depuis module_code à voir si on peux faire sans
    'site': MonitoringSite,
    'visit': MonitoringObject,
    'observation': MonitoringObject,
    'observation_detail': MonitoringObject,
    'sites_group': MonitoringObjectGeom,
}

monitoring_definitions.set(MonitoringObjects_dict, MonitoringModels_dict)
