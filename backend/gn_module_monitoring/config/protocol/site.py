from typing import ClassVar

from .base import BaseProtocolSchema


class SiteProtocolSchema(BaseProtocolSchema):
    # TODO: si sites_group fait partie du tree, alors site a par défaut un champs id_sites_group d’ajouté
    # voir SITES_GROUP_CONFIG et process_schema dans config/utils.py
    base_data: ClassVar = {
        "chained": True,
        "id_field_name": "id_base_site",
        "description_field_name": "base_site_name",
        "label": "Site",
        "label_list": "Sites",
        "genre": "M",
        "geom_field_name": "geom",
        "uuid_field_name": "uuid_base_site",
        "geometry_type": ["Point", "LineString", "Polygon"],
        "display_properties": [
            "base_site_name",
            "base_site_code",
            "base_site_description",
            "id_inventor",
            "first_use_date",
            "last_visit",
            "nb_visits",
            "altitude_min",
            "altitude_max",
            "types_site",
        ],
        "display_list": [
            "base_site_name",
            "base_site_code",
            "last_visit",
            "id_inventor",
            "nb_visits",
            "types_site",
            "nb_individuals",
        ],
        "sorts": [{"prop": "last_visit", "dir": "desc"}],
        "fields": {
            "id_base_site": {"type_widget": "number", "attribut_label": "Id site", "hidden": True},
            "base_site_code": {"type_widget": "text", "attribut_label": "Code", "required": True},
            "base_site_name": {"type_widget": "text", "attribut_label": "Nom", "required": True},
            "base_site_description": {"type_widget": "textarea", "attribut_label": "Description"},
            "id_inventor": {
                "type_widget": "observers",
                "attribut_label": "Observateur",
                "type_util": "user",
                "code_list": "CODE_OBSERVERS_LIST",
                "required": True,
                "multi_select": False,
            },
            "id_digitiser": {
                "attribut_label": "Digitiser",
                "type_util": "user",
                "required": True,
                "hidden": True,
            },
            "first_use_date": {
                "type_widget": "date",
                "attribut_label": "Date description",
                "required": True,
            },
            "last_visit": {
                "attribut_label": "Dernière visite",
                "type_widget": "date",
                "hidden": True,
            },
            "nb_visits": {
                "attribut_label": "Nb. visites",
                "type_widget": "number",
                "hidden": True,
            },
            "nb_individuals": {
                "attribut_label": "Nb. individus",
                "type_widget": "number",
                "hidden": True,
            },
            "uuid_base_site": {
                "attribut_label": "uuid",
                "type_widget": "text",
                "type_util": "uuid",
                "hidden": True,
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_base_sites",
            },
            "altitude_min": {
                "type_widget": "number",
                "attribut_label": "Altitude (min)",
                "hidden": True,
            },
            "altitude_max": {
                "type_widget": "number",
                "attribut_label": "Altitude (max)",
                "hidden": True,
            },
            "types_site": {
                "type_widget": "datalist",
                "attribut_label": "Type(s) de site",
                "type_util": "types_site",
                "keyValue": "id_nomenclature_type_site",
                "keyLabel": "label",
                "multiple": True,
                "api": "__MONITORINGS_PATH/modules/__MODULE.MODULE_CODE/types_sites",
                "application": "GeoNature",
                "required": True,
                "nullDefault": True,
                "definition": "Permet de n'avoir que les types de site lié au module",
                "designStyle": "bootstrap",
            },
        },
    }
