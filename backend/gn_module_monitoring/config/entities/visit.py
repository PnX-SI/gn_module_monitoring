from typing import ClassVar

from .base import BaseEntityConfigSchema


class VisitEntityConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
        "id_field_name": "id_base_visit",
        "chained": True,
        "description_field_name": "visit_date_min",
        "label": "Visite",
        "genre": "F",
        "uuid_field_name": "uuid_base_visit",
        "label_list": "Visites",
        "display_properties": [
            "id_base_site",
            "visit_date_min",
            "observers",
            "comments",
            "nb_observations",
        ],
        "display_list": [
            "id_base_site",
            "visit_date_min",
            "observers",
            "comments",
            "nb_observations",
        ],
        "sorts": [{"prop": "visit_date_min", "dir": "desc"}],
        "fields": {
            "id_base_site": {
                "store": {"type": "site"},
                "widget": {"attribut_label": "ID SITE", "hidden": True},
            },
            "id_module": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "ID Module", "hidden": True},
                "required": True,
            },
            "observers": {
                "store": {
                    "type": "users",
                    "code_list": "__MODULE.CODE_OBSERVERS_LIST",
                },
                "widget": {
                    "type": "observers",
                    "attribut_label": "Observateurs",
                    "multiple": True,
                    "hidden": False,
                },
                "required": True,
            },
            "observers_txt": {
                "store": {"type": "string"},
                "widget": {
                    "type": "observers-text",
                    "attribut_label": "Observateur(s) (extérieur)",
                    "hidden": True,
                },
                "required": False,
            },
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {"attribut_label": "Digitiser", "hidden": True},
                "required": False,
            },
            "visit_date_min": {
                "store": {"type": "datetime"},
                "widget": {"type": "date", "attribut_label": "Date"},
                "required": True,
            },
            "visit_date_max": {
                "store": {"type": "datetime"},
                "widget": {"type": "date", "attribut_label": "Date (max)", "hidden": True},
            },
            "id_nomenclature_tech_collect_campanule": {
                "store": {
                    "type": "nomenclature",
                    "nomenclature_type": "TECHNIQUE_OBS",
                }
            },
            "comments": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Commentaires"},
            },
            "uuid_base_visit": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "id_dataset": {
                "store": {"type": "dataset"},
                "widget": {
                    "type": "dataset",
                    "attribut_label": "Jeu de données",
                    "module_code": "__MODULE.MODULE_CODE",
                    "creatable_in_module": "__MODULE.MODULE_CODE.MONITORINGS_VISITES",
                },
                "required": True,
            },
            "nb_observations": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Nombre d'observations", "hidden": True},
            },
            "medias": {
                "store": {"type": "dummy"},
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_base_visits",
                },
            },
        },
    }
