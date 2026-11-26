from typing import ClassVar

from .base import BaseEntityConfigSchema


class ObservationEntityConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
        "id_field_name": "id_observation",
        "description_field_name": "id_observation",
        "chained": True,
        "label": "Observation",
        "label_list": "Observations",
        "genre": "F",
        "display_properties": ["cd_nom", "comments"],
        "uuid_field_name": "uuid_observation",
        "fields": {
            "id_base_visit": {
                "store": {"type": "visit"},
                "widget": {"attribut_label": "Id visite", "hidden": True},
                "required": True,
            },
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {"attribut_label": "Numérisateur", "hidden": True},
                "required": True,
            },
            "id_individual": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Id individu", "hidden": True},
            },
            "cd_nom": {
                "store": {"type": "taxonomy"},
                "widget": {
                    "type": "taxonomy",
                    "attribut_label": "Espèce",
                    "id_list": "__MODULE.ID_LIST_TAXONOMY",
                },
                "required": True,
            },
            "comments": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Commentaires"},
            },
            "uuid_observation": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "medias": {
                "store": {"type": "dummy"},
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_observations",
                },
            },
        },
    }
