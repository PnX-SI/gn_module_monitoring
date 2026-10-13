from typing import ClassVar

from gn_module_monitoring.monitoring.models import TMonitoringIndividuals
from gn_module_monitoring.monitoring.schemas import MonitoringIndividualsSchema

from .base import BaseEntityConfigSchema


class IndividualConfigSchema(BaseEntityConfigSchema):
    base_data: ClassVar = {
        "id_field_name": "id_individual",
        "description_field_name": "individual_name",
        "chained": True,
        "filters": {"active": True},
        "label": "Individu",
        "label_list": "Individus",
        "genre": "M",
        "display_properties": [
            "uuid_individual",
            "individual_name",
            "active",
            "id_nomenclature_sex",
            "comment",
            "cd_nom",
            "id_digitiser",
            "id_operator",
        ],
        "display_list": ["individual_name", "uuid_individual", "active", "nb_sites"],
        "uuid_field_name": "uuid_individual",
        "generic": {
            "id_individual": {
                "type_widget": "text",
                "attribut_label": "Id individual",
                "hidden": True,
            },
            "nb_sites": {"attribut_label": "Nombre de sites associés"},
            "uuid_individual": {
                "attribut_label": "uuid",
                "type_widget": "text",
                "type_util": "uuid",
                "hidden": True,
            },
            "individual_name": {
                "type_widget": "text",
                "attribut_label": "Nom de l'individu",
                "required": True,
            },
            "id_nomenclature_sex": {
                "type_widget": "nomenclature",
                "attribut_label": "Sexe",
                "code_nomenclature_type": "SEXE",
                "type_util": "nomenclature",
            },
            "active": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Actif",
                "definition": "Activer cet individu",
                "value": True,
            },
            "comment": {"type_widget": "textarea", "attribut_label": "Commentaires"},
            "cd_nom": {
                "type_widget": "taxonomy",
                "attribut_label": "Espèce",
                "type_util": "taxonomy",
                "id_list": "__MODULE.ID_LIST_TAXONOMY",
                "required": "({value}) => '__MODULE.CD_NOM' === 'None'",
                "hidden": "({value}) => '__MODULE.CD_NOM' !== 'None'",
            },
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
                "schema_dot_table": "gn_monitoring.t_individuals",
            },
        },
        "change": [
            "({objForm, meta}) => {",
            "const cd_nom = __MODULE.CD_NOM",
            "if (!objForm.controls.cd_nom.dirty) {",
            "objForm.patchValue({cd_nom: cd_nom})",
            "}",
            "}",
            "",
        ],
    }
