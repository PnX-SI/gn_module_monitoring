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
