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

from .base import monitoring_definitions, monitoring_g_definitions
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
    'observation_detail': TMonitoringObservationDetails,
    'sites_group': TMonitoringSitesGroups,
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

# #####################""
MonitoringModelsG_dict = {
    x: MonitoringModels_dict[x] for x in MonitoringModels_dict if x not in "module"
}

MonitoringObjectsG_dict = {
    x: MonitoringObjects_dict[x] for x in MonitoringObjects_dict if x not in "module"
}

monitoring_g_definitions.set(MonitoringObjectsG_dict, MonitoringModelsG_dict)
