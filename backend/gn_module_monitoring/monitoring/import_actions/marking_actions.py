from gn_module_monitoring.monitoring.import_actions.base import BaseImportActions


class MarkingImportActions(BaseImportActions):
    ENTITY_CODE = "marking"
    FIELD_PREFIX = "m__"
    ID_FIELD = "id_marking"
    UUID_FIELD = "uuid_marking"
