import json

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.tools.utils import schema_context

from .module import ModuleProtocolSchema
from .sites_group import SitesGroupProtocolSchema
from .site import SiteProtocolSchema
from .visit import VisitProtocolSchema
from .observation import ObservationProtocolSchema
from .observation_detail import ObservationDetailProtocolSchema


def load_protocol_entity_config(module_code, entity):
    """
    Raises:
        UnicodeDecodeError
        JSONDecodeError
        ValidationError
    """
    if entity == "module":
        schema = ModuleProtocolSchema()
    elif entity == "sites_group":
        schema = SitesGroupProtocolSchema()
    elif entity == "site":
        schema = SiteProtocolSchema()
    elif entity == "visit":
        schema = VisitProtocolSchema()
    elif entity == "observation":
        schema = ObservationProtocolSchema()
    elif entity == "observation_detail":
        schema = ObservationDetailProtocolSchema()
    # TODO: individual, marking
    else:
        raise NotImplementedError

    with schema_context(entity=entity):
        config_path = monitoring_module_config_path(module_code) / f"{entity}.json"
        if config_path.is_file():
            with config_path.open() as f:
                entity_config = json.load(f)
        else:
            entity_config = {}

        #     # TODO: remplacer les templates (__MONITORINGS_PATH, etc.)
        return schema.load(entity_config)
