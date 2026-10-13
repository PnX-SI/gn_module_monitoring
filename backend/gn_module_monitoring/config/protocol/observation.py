from typing import ClassVar

from gn_module_monitoring.monitoring.models import TMonitoringObservations
from gn_module_monitoring.monitoring.schemas import MonitoringObservationsSchema

from .base import BaseProtocolSchema


class ObservationProtocolSchema(BaseProtocolSchema):
    base_data: ClassVar = {
        "id_field_name": "id_observation",
        "description_field_name": "id_observation",
        "chained": True,
        "label": "Observation",
        "label_list": "Observations",
        "genre": "F",
        "display_properties": ["cd_nom", "comments"],
        "uuid_field_name": "uuid_observation",
        "fields": {
            "id_observation": {
                "type_widget": "number",
                "attribut_label": "Id observation",
                "hidden": True,
            },
            "id_base_visit": {
                "type_widget": "number",
                "attribut_label": "Id visite",
                "hidden": True,
            },
            "id_digitiser": {
                "attribut_label": "Numérisateur",
                "required": True,
                "hidden": True,
                "type_util": "user",
            },
            "id_individual": {
                "type_widget": "text",
                "attribut_label": "Id individu",
                "hidden": True,
            },
            "cd_nom": {
                "type_widget": "taxonomy",
                "attribut_label": "Espèce",
                "type_util": "taxonomy",
                "required": True,
                "id_list": "__MODULE.ID_LIST_TAXONOMY",
            },
            "comments": {"type_widget": "text", "attribut_label": "Commentaires"},
            "uuid_observation": {
                "attribut_label": "uuid",
                "type_widget": "text",
                "type_util": "uuid",
                "hidden": True,
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_observations",
            },
        },
    }


class ObservationService:
    model = TMonitoringObservations
    model_schema = MonitoringObservationsSchema
    config_schema = ObservationProtocolSchema
