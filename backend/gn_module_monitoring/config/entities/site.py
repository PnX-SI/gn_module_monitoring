from copy import deepcopy
from typing import ClassVar

import marshmallow as ma
from marshmallow import post_load

from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.utils.routes import query_all_types_site_from_module_id

from .base import BaseEntityConfigSchema


class SiteEntityConfigSchema(BaseEntityConfigSchema):
    types_site = ma.fields.Dict(dump_only=True)

    @post_load
    def load_types_site(self, data, **kwargs):
        # for frontend
        module = schema_context.get()["entity"].module
        id_module = module.module.id_module if module.module else None
        data["types_site"] = {
            t.id_nomenclature_type_site: {"name": t.nomenclature.label_default}
            for t in query_all_types_site_from_module_id(id_module)
        }
        return data

    default_config: ClassVar = {
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
                "store": {"type": "integer"},
                "widget": {
                    "attribut_label": "Altitude (min)",
                    "hidden": True,
                },
            },
            "altitude_max": {
                "store": {"type": "integer"},
                "widget": {
                    "attribut_label": "Altitude (max)",
                    "hidden": True,
                },
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

    def get_default_config(self):
        entity = schema_context.get()["entity"]
        config = deepcopy(self.default_config)
        if "sites_group" in entity.module.entities_list:
            # si sites_group fait partie du tree, alors site a par défaut un champs id_sites_group d’ajouté
            config["fields"]["id_sites_group"] = {
                "type_widget": "datalist",
                "attribut_label": "Groupe de sites",
                "type_util": "sites_group",
                "keyValue": "id_sites_group",
                "keyLabel": "sites_group_name",
                "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/sites_group?id_module=__MODULE.ID_MODULE&fields=id_sites_group&fields=sites_group_name",
                "application": "GeoNature",
            }
        return config
