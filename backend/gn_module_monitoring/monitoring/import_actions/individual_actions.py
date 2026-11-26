from gn_module_monitoring.monitoring.import_actions.base import BaseImportActions


class IndividualImportActions(BaseImportActions):
    ENTITY_CODE = "individual"
    FIELD_PREFIX = "i__"
    ID_FIELD = "id_individual"
    UUID_FIELD = "uuid_individual"
