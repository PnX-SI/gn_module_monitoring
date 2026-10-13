from typing import ClassVar

from gn_module_monitoring.monitoring.models import TMonitoringMarkingEvent
from gn_module_monitoring.monitoring.schemas import MonitoringMarkingSchema

from .base import BaseProtocolSchema


class MarkingProtocolSchema(BaseProtocolSchema):
    base_data: ClassVar = {
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
            "id_marking": {"type_widget": "text", "attribut_label": "Id marquage", "hidden": True},
            "id_individual": {
                "type_widget": "individuals",
                "attribut_label": "Choix de l'individu",
                "id_module": "__MODULE.ID_MODULE",
                "hidden": True,
            },
            "marking_date": {
                "type_widget": "date",
                "attribut_label": "Date de marquage",
                "required": True,
            },
            "id_operator": {
                "type_widget": "datalist",
                "attribut_label": "Opérateur",
                "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
                "application": "GeoNature",
                "keyValue": "id_role",
                "keyLabel": "nom_complet",
                "type_util": "user",
                "required": True,
            },
            "id_base_marking_site": {
                "type_widget": "datalist",
                "attribut_label": "Site",
                "type_util": "site",
                "keyValue": "id_base_site",
                "keyLabel": "base_site_name",
                "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/site?id_module=__MODULE.ID_MODULE&fields=id_base_site&fields=base_site_name",
                "application": "GeoNature",
            },
            "id_nomenclature_marking_type": {
                "type_widget": "nomenclature",
                "attribut_label": "Type de marquage",
                "code_nomenclature_type": "TYP_MARQUAGE",
                "type_util": "nomenclature",
                "required": True,
            },
            "marking_location": {
                "type_widget": "text",
                "attribut_label": "Localisation du marquage",
            },
            "marking_code": {"type_widget": "text", "attribut_label": "Code du marquage"},
            "marking_details": {"type_widget": "text", "attribut_label": "Détails du marquage"},
            "id_digitiser": {
                "type_widget": "text",
                "attribut_label": "Numérisateur",
                "required": True,
                "hidden": True,
                "type_util": "user",
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_marking_events",
            },
        },
    }


class MarkingService:
    model = TMonitoringMarkingEvent
    model_schema = MonitoringMarkingSchema
    config_schema = MarkingProtocolSchema
