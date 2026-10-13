from typing import ClassVar

from .base import BaseProtocolSchema


class VisitProtocolSchema(BaseProtocolSchema):
    base_data: ClassVar = {
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
            "dataset",
            "nb_observations",
        ],
        "display_list": [
            "id_base_site",
            "visit_date_min",
            "observers",
            "comments",
            "dataset",
            "nb_observations",
        ],
        "sorts": [{"prop": "visit_date_min", "dir": "desc"}],
        "fields": {
            "id_base_visit": {"type_widget": "number", "attribut_label": "ID", "hidden": True},
            "id_base_site": {"type_widget": "number", "attribut_label": "ID SITE", "hidden": True},
            "id_module": {"type_widget": "text", "attribut_label": "ID Module", "hidden": True},
            "observers": {
                "type_widget": "observers",
                "attribut_label": "Observateurs",
                "type_util": "user",
                "code_list": "CODE_OBSERVERS_LIST",
                "multi_select": True,
                "hidden": False,
                "required": True,
            },
            "observers_txt": {
                "type_widget": "observers-text",
                "attribut_label": "Observateur(s) (extérieur)",
                "required": False,
                "hidden": True,
            },
            "id_digitiser": {
                "attribut_label": "Digitiser",
                "type_util": "user",
                "required": True,
                "hidden": True,
            },
            "visit_date_min": {"type_widget": "date", "attribut_label": "Date", "required": True},
            "visit_date_max": {
                "type_widget": "date",
                "attribut_label": "Date (max)",
                "hidden": True,
            },
            "comments": {"type_widget": "text", "attribut_label": "Commentaires"},
            "uuid_base_visit": {
                "attribut_label": "uuid",
                "type_widget": "text",
                "type_util": "uuid",
                "hidden": True,
            },
            "id_dataset": {
                "type_widget": "dataset",
                "type_util": "dataset",
                "attribut_label": "Jeu de données",
                "module_code": "__MODULE.MODULE_CODE",
                "creatable_in_module": "__MODULE.MODULE_CODE.MONITORINGS_VISITES",
                "required": True,
            },
            "nb_observations": {
                "type_widget": "number",
                "attribut_label": "Nombre d'observations",
                "hidden": True,
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_base_visits",
            },
        },
    }
