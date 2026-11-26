from typing import ClassVar

from .base import BaseEntityConfigSchema


class ObservationDetailEntityConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
        "id_field_name": "id_observation_detail",
        "description_field_name": "id_observation_detail",
        "chained": True,
        "label": "Observation détail",
        "label_list": "Observations détail",
        "genre": "F",
        "display_properties": ["uuid_observation_detail"],
        "uuid_field_name": "uuid_observation_detail",
        "fields": {
            "id_observation": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Id observation", "hidden": True},
                "required": True,
            },
            "uuid_observation_detail": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "medias": {
                "store": {"type": "dummy"},
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_observation_details",
                },
            },
        },
    }
