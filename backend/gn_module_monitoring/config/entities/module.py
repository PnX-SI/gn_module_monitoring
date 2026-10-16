from typing import ClassVar

from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.monitoring.schemas import MonitoringModuleSchema

from .base import BaseEntityConfigSchema


class ModuleConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
        "id_field_name": "id_module",
        "description_field_name": "module_label",
        "label": "Module",
        "genre": "M",
        "uuid_field_name": "uuid_module_complement",
        "display_properties": ["module_label", "module_desc", "datasets"],
        "fields": {
            "module_code": {
                "type_widget": "text",
                "attribut_label": "Code",
                "required": True,
                "hidden": True,
            },
            "module_label": {
                "type_widget": "text",
                "attribut_label": "Nom",
                "required": True,
                "hidden": True,
            },
            "module_path": {
                "type_widget": "text",
                "attribut_label": "Path",
                "required": True,
                "hidden": True,
            },
            "module_desc": {
                "type_widget": "text",
                "attribut_label": "Description",
                "required": True,
                "hidden": True,
            },
            "module_picto": {
                "type_widget": "text",
                "attribut_label": "Icone dans le menu",
                "required": True,
            },
            "uuid_module_complement": {"attribut_label": "uuid"},
            "datasets": {
                "type_widget": "dataset",
                "type_util": "dataset",
                "attribut_label": "Jeu de données",
                "required": True,
                "multi_select": True,
            },
            "id_list_observer": {
                "type_widget": "datalist",
                "attribut_label": "Liste des observateurs",
                "keyValue": "id_liste",
                "keyLabel": "nom_liste",
                "multiple": False,
                "api": "users/listes",
                "application": "GeoNature",
                "required": True,
                "type_util": "observer_list",
                "definition": "Liste des observateurs. À gérer dans UsersHub.",
                "designStyle": "bootstrap",
            },
            "id_list_taxonomy": {
                "type_widget": "datalist",
                "attribut_label": "Liste des taxons",
                "keyValue": "id_liste",
                "keyLabel": "nom_liste",
                "multiple": False,
                "api": "biblistes/",
                "application": "TaxHub",
                "required": True,
                "type_util": "taxonomy_list",
                "data_path": "data",
                "definition": "Liste des taxons. À gérer dans TaxHub.",
                "designStyle": "bootstrap",
            },
            "b_synthese": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Activer la synthèse ?",
                "definition": "Insertion automatique des nouvelles données dans la synthèse.",
            },
            "b_draw_sites_group": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Dessiner les groupes de sites",
                "definition": "Affichage des groupes de site en dessinant l'enveloppe des sites du groupe et en affichant l'aire du groupe de sites",
                "hidden": True,
            },
            "taxonomy_display_field_name": {
                "type_widget": "datalist",
                "attribut_label": "Affichage des taxons",
                "values": [
                    {"label": "Nom vernaculaire ou nom latin", "value": "nom_vern,lb_nom"},
                    {"label": "Nom latin", "value": "lb_nom"},
                ],
                "required": True,
                "designStyle": "bootstrap",
            },
            "cd_nom": {
                "attribut_label": "Espèce",
                "required": False,
                "hidden": True,
            },
            "active_frontend": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Afficher dans le menu ?",
                "definition": "Afficher le module dans le menu de GeoNature. (Recharger la page pour voir les modifications).",
            },
            "types_site": {
                "type_widget": "datalist",
                "attribut_label": "Types de sites",
                "type_util": "types_site",
                "keyValue": "id_nomenclature_type_site",
                "keyLabel": "label",
                "multiple": True,
                "api": "__MONITORINGS_PATH/sites/types",
                "application": "GeoNature",
                "required": True,
                "data_path": "items",
                "definition": "Permet de paramétrer la compatibilité de ce module avec les types de sites",
                "designStyle": "bootstrap",
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_module_complements",
            },
        },
    }
