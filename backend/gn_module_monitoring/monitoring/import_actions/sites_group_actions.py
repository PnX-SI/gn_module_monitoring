from gn_module_monitoring.monitoring.import_actions.base import BaseImportActions


class SitesGroupImportActions(BaseImportActions):
    ENTITY_CODE = "sites_group"
    FIELD_PREFIX = "g__"
    ID_FIELD = "id_sites_group"
    UUID_FIELD = "uuid_sites_group"
