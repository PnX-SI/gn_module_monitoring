from typing import ClassVar

from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema

from .base import BaseEntityConfigSchema


class SitesGroupConfigSchema(BaseEntityConfigSchema):
    base_data: ClassVar = {
        "id_field_name": "id_sites_group",
        "chained": True,
        "description_field_name": "sites_group_name",
        "label": "Groupe de sites",
        "label_list": "Groupes de sites",
        "genre": "M",
        "uuid_field_name": "uuid_sites_group",
        "geom_field_name": "geom",
        "geometry_type": "Polygon",
        "display_properties": [
            "sites_group_name",
            "sites_group_code",
            "modules",
            "nb_sites",
            "nb_visits",
            "comments",
        ],
        "sorts": [{"prop": "sites_group_code"}],
        "fields": {
            "id_sites_group": {"type_widget": "text", "attribut_label": "Id site", "hidden": True},
            "sites_group_name": {"type_widget": "text", "attribut_label": "Nom", "required": True},
            "sites_group_code": {
                "type_widget": "text",
                "attribut_label": "Code",
                "required": True,
            },
            "sites_group_description": {
                "type_widget": "textarea",
                "attribut_label": "Description",
            },
            "comments": {"type_widget": "text", "attribut_label": "Commentaires"},
            "uuid_sites_group": {
                "attribut_label": "uuid",
                "type_widget": "text",
                "type_util": "uuid",
                "hidden": True,
            },
            "nb_sites": {
                "attribut_label": "Nombre de sites",
                "type_widget": "number",
                "hidden": True,
            },
            "nb_visits": {
                "attribut_label": "Nombre de visites",
                "type_widget": "number",
                "hidden": True,
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_sites_groups",
            },
            "altitude_min": {
                "type_widget": "number",
                "step": 1,
                "attribut_label": "Altitude (min)",
                "hidden": True,
            },
            "altitude_max": {
                "type_widget": "number",
                "step": 1,
                "attribut_label": "Altitude (max)",
                "hidden": True,
            },
            "id_digitiser": {
                "attribut_label": "Digitiser",
                "type_util": "user",
                "required": True,
                "hidden": True,
            },
            "modules": {
                "type_widget": "datalist",
                "type_util": "module",
                "attribut_label": "Modules",
                "keyValue": "id_module",
                "keyLabel": "module_label",
                "multiple": True,
                "default": [{"id_module": "__MODULE.ID_MODULE"}],
                "api": "monitorings/modules",
                "application": "GeoNature",
                "required": True,
                "designStyle": "bootstrap",
                "definition": "Permet de contrôler dans quel(s) module(s) les groupes de site remonteront",
            },
        },
    }
