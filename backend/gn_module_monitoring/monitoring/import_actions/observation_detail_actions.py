from gn_module_monitoring.monitoring.import_actions.base import BaseImportActions


class ObservationDetailImportActions(BaseImportActions):
    ENTITY_CODE = "observation_detail"
    FIELD_PREFIX = "d__"
    ID_FIELD = "id_observation_detail"
    UUID_FIELD = "uuid_observation_detail"
