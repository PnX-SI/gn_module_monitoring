from .module import ModuleService
from .sites_group import SitesGroupService
from .site import SiteService
from .visit import VisitService
from .observation import ObservationService
from .observation_detail import ObservationDetailService
from .individual import IndividualService
from .marking import MarkingService

SERVICE_MAP = {
    "module": ModuleService,
    "sites_group": SitesGroupService,
    "site": SiteService,
    "visit": VisitService,
    "observation": ObservationService,
    "observation_detail": ObservationDetailService,
    "individual": IndividualService,
    "marking": MarkingService,
}
