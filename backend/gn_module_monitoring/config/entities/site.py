from copy import deepcopy
from typing import ClassVar

import marshmallow as ma
from marshmallow import post_load, pre_load

from gn_module_monitoring.tools.utils import schema_context

from .base import BaseEntityConfigSchema


class SiteEntityConfigSchema(BaseEntityConfigSchema):
    types_site = ma.fields.Dict(dump_only=True)

    @pre_load
    def pre_load(self, data, **kwargs):
        # Les champs des types de site sont fusionnés avant ceux du protocole (le type de site l’emporte)
        data["fields"] = data.get("fields", {})
        for ts in schema_context.get()["entity"].module.module.types_site:
            config = ts.config or {}
            fields = {**config.get("specific", {}), **config.get("fields", {})}
            # Les champs du protocole sont écrasé par
            for field_name, field_spec in fields.items():
                data["fields"].setdefault(field_name, {}).update(field_spec)
        return super().pre_load(data, **kwargs)

    @post_load
    def load_types_site_ids_for_fields(self, data, **kwargs):
        """
        This hook:
            - Add types_site to config.
            - Add id_types_site to all fields which comes from types site.
        """
        data["types_site"] = {}
        for ts in schema_context.get()["entity"].module.module.types_site:
            config = ts.config or {}
            fields = {**config.get("specific", {}), **config.get("fields", {})}
            for field_name in fields:
                data["fields"][field_name].setdefault("id_types_site", []).append(
                    ts.id_nomenclature_type_site
                )
            data["types_site"][ts.id_nomenclature_type_site] = {
                "name": ts.nomenclature.label_default
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
            "base_site_code": {
                "widget": {"type": "text", "attribut_label": "Code"},
                "required": True,
            },
            "base_site_name": {
                "widget": {"type": "text", "attribut_label": "Nom"},
                "required": True,
            },
            "base_site_description": {
                "widget": {"type": "textarea", "attribut_label": "Description"},
            },
            "id_inventor": {
                "store": {
                    "type": "user",
                    "code_list": "__MODULE.CODE_OBSERVERS_LIST",
                },
                "widget": {
                    "type": "observers",
                    "attribut_label": "Observateur",
                    "multi_select": False,
                },
                "required": True,
            },
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {"attribut_label": "Digitiser", "hidden": True},
                "required": True,
            },
            "first_use_date": {
                "store": {"type": "datetime"},
                "widget": {"attribut_label": "Date description"},
                "required": True,
            },
            "last_visit": {
                "widget": {"type": "date", "attribut_label": "Dernière visite", "hidden": True},
            },
            "nb_visits": {
                "widget": {"type": "number", "attribut_label": "Nb. visites", "hidden": True},
            },
            "nb_individuals": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Nb. individus", "hidden": True},
            },
            "uuid_base_site": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "medias": {
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_base_sites",
                },
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
                "store": {"type": "types_site"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Type(s) de site",
                    "keyValue": "id_nomenclature_type_site",
                    "keyLabel": "label",
                    "multiple": True,
                    "api": "__MONITORINGS_PATH/modules/__MODULE.MODULE_CODE/types_sites",
                    "application": "GeoNature",
                    "nullDefault": True,
                    "definition": "Permet de n'avoir que les types de site lié au module",
                    "designStyle": "bootstrap",
                },
                "required": True,
            },
        },
    }

    def get_default_config(self):
        entity = schema_context.get()["entity"]
        config = deepcopy(self.default_config)
        if "sites_group" in entity.module.entities_list:
            # si sites_group fait partie du tree, alors site a par défaut un champs id_sites_group d’ajouté
            config["fields"]["id_sites_group"] = {
                "store": {"type": "sites_group"},
                "widget": {
                    "attribut_label": "Groupe de sites",
                    "hidden": True,
                    "keyValue": "id_sites_group",
                    "keyLabel": "sites_group_name",
                    "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/sites_group?id_module=__MODULE.ID_MODULE&fields=id_sites_group&fields=sites_group_name",
                    "application": "GeoNature",
                },
            }
        return config
