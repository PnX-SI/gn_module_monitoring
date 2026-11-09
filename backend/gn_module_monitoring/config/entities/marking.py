from typing import ClassVar

from .base import BaseEntityConfigSchema


class MarkingEntityConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
        "id_field_name": "id_marking",
        "description_field_name": "id_marking",
        "chained": True,
        "label": "Marquage",
        "label_list": "Marquages",
        "genre": "M",
        "display_properties": ["marking_location", "marking_code", "marking_details"],
        "display_list": [
            "marking_location",
            "marking_code",
            "marking_details",
            "id_nomenclature_marking_type",
            "id_base_marking_site",
            "id_operator",
        ],
        "uuid_field_name": "id_marking",
        "fields": {
            "id_marking": {
                "widget": {
                    "type": "number",
                    "step": 1,
                    "attribut_label": "Id marquage",
                    "hidden": True,
                },
            },
            "id_individual": {
                "widget": {
                    "type": "individuals",
                    "attribut_label": "Choix de l'individu",
                    "id_module": "__MODULE.ID_MODULE",
                    "hidden": True,
                },
            },
            "marking_date": {
                "store": {"type": "datetime"},
                "widget": {"type": "date", "attribut_label": "Date de marquage"},
                "required": True,
            },
            "id_operator": {
                "store": {"type": "user"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Opérateur",
                    "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
                    "application": "GeoNature",
                    "keyValue": "id_role",
                    "keyLabel": "nom_complet",
                },
                "required": True,
            },
            "id_base_marking_site": {
                "store": {"type": "site"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Site",
                    "keyValue": "id_base_site",
                    "keyLabel": "base_site_name",
                    "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/site?id_module=__MODULE.ID_MODULE&fields=id_base_site&fields=base_site_name",
                    "application": "GeoNature",
                },
            },
            "id_nomenclature_marking_type": {
                "store": {
                    "type": "nomenclature",
                    "nomenclature_type": "TYP_MARQUAGE",
                },
                "widget": {
                    "type": "nomenclature",
                    "attribut_label": "Type de marquage",
                },
                "required": True,
            },
            "marking_location": {
                "widget": {"type": "text", "attribut_label": "Localisation du marquage"},
            },
            "marking_code": {"widget": {"type": "text", "attribut_label": "Code du marquage"}},
            "marking_details": {"widget": {"type": "text", "attribut_label": "Détails du marquage"}},
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {
                    "type": "user",
                    "attribut_label": "Numérisateur",
                    "hidden": True,
                },
                "required": True,
            },
            "medias": {
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_marking_events",
                },
            },
        },
    }
