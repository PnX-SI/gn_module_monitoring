from typing import ClassVar

from .base import BaseProtocolSchema


class ObservationDetailProtocolSchema(BaseProtocolSchema):
    base_data: ClassVar = {
        "id_field_name": "id_observation_detail",
        "description_field_name": "id_observation_detail",
        "chained": True,
        "label": "Observation détail",
        "label_list": "Observations détail",
        "genre": "F",
        "display_properties": ["uuid_observation_detail"],
        "uuid_field_name": "uuid_observation_detail",
        "fields": {
            "id_observation_detail": {
                "type_widget": "text",
                "attribut_label": "Id observation",
                "hidden": True,
            },
            "id_observation": {"attribut_label": "Id visite", "type_util": "user", "hidden": True},
            "uuid_observation_detail": {
                "attribut_label": "uuid",
                "type_widget": "text",
                "type_util": "uuid",
                "hidden": True,
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_observation_details",
            },
        },
    }
