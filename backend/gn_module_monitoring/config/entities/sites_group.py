from typing import ClassVar

from .base import BaseEntityConfigSchema


class SitesGroupEntityConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
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
            "id_sites_group": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Id site", "hidden": True},
            },
            "sites_group_name": {
                "widget": {"type": "text", "attribut_label": "Nom"},
                "required": False,
            },
            "sites_group_code": {
                "widget": {"type": "text", "attribut_label": "Code"},
                "required": False,
            },
            "sites_group_description": {
                "widget": {"type": "textarea", "attribut_label": "Description"},
            },
            "comments": {"widget": {"type": "text", "attribut_label": "Commentaires"}},
            "uuid_sites_group": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "nb_sites": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Nombre de sites", "hidden": True},
            },
            "nb_visits": {
                "widget": {"type": "number", "attribut_label": "Nombre de visites", "hidden": True},
            },
            "medias": {
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_sites_groups",
                },
            },
            "altitude_min": {
                "widget": {
                    "type": "number",
                    "step": 1,
                    "attribut_label": "Altitude (min)",
                    "hidden": True,
                },
            },
            "altitude_max": {
                "widget": {
                    "type": "number",
                    "step": 1,
                    "attribut_label": "Altitude (max)",
                    "hidden": True,
                },
            },
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {"attribut_label": "Digitiser", "hidden": True},
                "required": False,
            },
            "modules": {
                "store": {"type": "modules"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Modules",
                    "keyValue": "id_module",
                    "keyLabel": "module_label",
                    "multiple": True,
                    "default": [{"id_module": "__MODULE.ID_MODULE"}],
                    "api": "monitorings/modules",
                    "application": "GeoNature",
                    "designStyle": "bootstrap",
                    "definition": "Permet de contrôler dans quel(s) module(s) les groupes de site remonteront",
                },
                "required": True,
            },
        },
    }
