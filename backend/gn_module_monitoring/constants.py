from enum import Enum


class ObjectType(str, Enum):
    """
    Types d'objets monitoring.
    """

    MODULE = "module"
    SITES_GROUP = "sites_group"
    SITE = "site"
    VISIT = "visit"
    OBSERVATION = "observation"
    OBSERVATION_DETAIL = "observation_detail"
    INDIVIDUAL = "individual"
    MARKING = "marking"

    def __str__(self):
        return self.value


# Objets de permission associés à chaque type d'objet monitoring
PERMISSION_OBJECT_CODES = {
    ObjectType.MODULE: "MONITORINGS_MODULES",
    ObjectType.SITE: "MONITORINGS_SITES",
    ObjectType.SITES_GROUP: "MONITORINGS_GRP_SITES",
    ObjectType.VISIT: "MONITORINGS_VISITES",
    ObjectType.OBSERVATION: "MONITORINGS_VISITES",
    ObjectType.OBSERVATION_DETAIL: "MONITORINGS_VISITES",
    ObjectType.INDIVIDUAL: "INDIVIDUALS",
    ObjectType.MARKING: "MONITORINGS_MARKINGS",
}
