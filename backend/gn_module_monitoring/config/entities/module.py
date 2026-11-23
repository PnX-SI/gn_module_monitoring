from typing import ClassVar

import marshmallow as ma
from marshmallow import post_load

from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.utils.routes import query_all_types_site_from_module_id

from .base import BaseEntityConfigSchema


class ModuleEntityConfigSchema(BaseEntityConfigSchema):
    root_object = ma.fields.Boolean(dump_only=True, dump_default=True)
    types_site = ma.fields.Dict(dump_only=True)
    # Lu par le frontend (monitoring-geom-component.ts) pour le bouton "Téléchargements"
    export_csv = ma.fields.Raw()
    # Lus par la commande d'installation (command/cmd.py) et stockés dans TMonitoringModules
    module_label = ma.fields.Str()
    module_desc = ma.fields.Str()
    b_draw_sites_group = ma.fields.Boolean()

    @post_load
    def load_types_site(self, data, **kwargs):
        # FIXME: retro-compat for frontend
        module = schema_context.get()["entity"].module
        id_module = module.module.id_module if module.module else None
        data["types_site"] = {
            t.id_nomenclature_type_site: {"name": t.nomenclature.label_default}
            for t in query_all_types_site_from_module_id(id_module)
        }
        return data

    default_config: ClassVar = {
        "id_field_name": "id_module",
        "description_field_name": "module_label",
        "label": "Module",
        "genre": "M",
        "uuid_field_name": "uuid_module_complement",
        "display_properties": ["module_label", "module_desc", "datasets"],
        "fields": {
            "module_code": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Code", "hidden": True},
                "required": True,
            },
            "module_label": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Nom", "hidden": True},
                "required": True,
            },
            "module_path": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Path", "hidden": True},
                "required": True,
            },
            "module_desc": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Description", "hidden": True},
                "required": True,
            },
            "module_picto": {
                "store": {"type": "string"},
                "widget": {"type": "text", "attribut_label": "Icone dans le menu"},
                "required": True,
            },
            "uuid_module_complement": {
                "store": {"type": "uuid"},
                "widget": {"attribut_label": "uuid"}
            },
            "datasets": {
                "store": {"type": "datasets"},
                "widget": {
                    "type": "dataset",
                    "attribut_label": "Jeu de données",
                    "multiple": True,
                },
                "required": True,
            },
            "id_list_observer": {
                "store": {"type": "observer_list"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Liste des observateurs",
                    "keyValue": "id_liste",
                    "keyLabel": "nom_liste",
                    "multiple": False,
                    "api": "users/listes",
                    "application": "GeoNature",
                    "definition": "Liste des observateurs. À gérer dans UsersHub.",
                    "designStyle": "bootstrap",
                },
                "required": True,
            },
            "id_list_taxonomy": {
                "store": {"type": "taxonomy_list"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Liste des taxons",
                    "keyValue": "id_liste",
                    "keyLabel": "nom_liste",
                    "multiple": False,
                    "api": "biblistes/",
                    "application": "TaxHub",
                    "data_path": "data",
                    "definition": "Liste des taxons. À gérer dans TaxHub.",
                    "designStyle": "bootstrap",
                },
                "required": True,
            },
            "b_synthese": {
                "store": {"type": "bool"},
                "widget": {
                    "type": "bool_checkbox",
                    "attribut_label": "Activer la synthèse ?",
                    "definition": "Insertion automatique des nouvelles données dans la synthèse.",
                },
            },
            "b_draw_sites_group": {
                "store": {"type": "bool"},
                "widget": {
                    "type": "bool_checkbox",
                    "attribut_label": "Dessiner les groupes de sites",
                    "definition": "Affichage des groupes de site en dessinant l'enveloppe des sites du groupe et en affichant l'aire du groupe de sites",
                    "hidden": True,
                },
            },
            "taxonomy_display_field_name": {
                "store": {
                    "type": "value",
                    "values": [
                        {"label": "Nom vernaculaire ou nom latin", "value": "nom_vern,lb_nom"},
                        {"label": "Nom latin", "value": "lb_nom"},
                    ],
                },
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Affichage des taxons",
                    "values": [
                        {"label": "Nom vernaculaire ou nom latin", "value": "nom_vern,lb_nom"},
                        {"label": "Nom latin", "value": "lb_nom"},
                    ],
                    "designStyle": "bootstrap",
                },
                "required": True,
            },
            "cd_nom": {
                "store": {"type": "taxonomy"},
                "widget": {"attribut_label": "Espèce", "hidden": True},
                "required": False,
            },
            "active_frontend": {
                "store": {"type": "bool"},
                "widget": {
                    "type": "bool_checkbox",
                    "attribut_label": "Afficher dans le menu ?",
                    "definition": "Afficher le module dans le menu de GeoNature. (Recharger la page pour voir les modifications).",
                },
            },
            "types_site": {
                "store": {"type": "types_site"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Types de sites",
                    "keyValue": "id_nomenclature_type_site",
                    "keyLabel": "label",
                    "multiple": True,
                    "api": "__MONITORINGS_PATH/sites/types",
                    "application": "GeoNature",
                    "data_path": "items",
                    "definition": "Permet de paramétrer la compatibilité de ce module avec les types de sites",
                    "designStyle": "bootstrap",
                },
                "required": True,
            },
            "medias": {
                "store": {"type": "dummy"},
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_module_complements",
                },
            },
        },
    }
