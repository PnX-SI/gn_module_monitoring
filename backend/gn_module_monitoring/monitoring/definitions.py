from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringObservationDetails,
    TMonitoringSitesGroups,
    TMonitoringIndividuals,
    TMonitoringMarkingEvent,
)
from gn_module_monitoring.monitoring.objects import (
    MonitoringModule,
    MonitoringSite,
    MonitoringIndividual,
)
from gn_module_monitoring.monitoring.base import monitoring_definitions
from gn_module_monitoring.monitoring.repositories import MonitoringObject
from gn_module_monitoring.monitoring.geom import MonitoringObjectGeom


"""
    MonitoringModels_dict :
    Fait le lien entre les monitoring_objects
    et les modèles sqlalchemy
"""

MonitoringModels_dict = {
    "module": TMonitoringModules,
    "site": TMonitoringSites,
    "visit": TMonitoringVisits,
    "observation": TMonitoringObservations,
    "observation_detail": TMonitoringObservationDetails,
    "sites_group": TMonitoringSitesGroups,
    "individual": TMonitoringIndividuals,
    "marking": TMonitoringMarkingEvent,
}

MonitoringObjects_dict = {
    "module": MonitoringModule,  # besoin pour retrouver le module depuis module_code à voir si on peux faire sans
    "site": MonitoringSite,
    "visit": MonitoringObject,
    "observation": MonitoringObject,
    "observation_detail": MonitoringObject,
    "sites_group": MonitoringObjectGeom,
    "individual": MonitoringIndividual,
    "marking": MonitoringObject,
}

monitoring_definitions.set(MonitoringObjects_dict, MonitoringModels_dict)
