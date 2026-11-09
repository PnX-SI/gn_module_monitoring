from typing import ClassVar

from .base import BaseEntityConfigSchema


class IndividualEntityConfigSchema(BaseEntityConfigSchema):
    default_config: ClassVar = {
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
                "widget": {"type": "text", "attribut_label": "Id individual", "hidden": True},
            },
            "nb_sites": {"widget": {"attribut_label": "Nombre de sites associés"}},
            "uuid_individual": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "individual_name": {
                "widget": {"type": "text", "attribut_label": "Nom de l'individu"},
                "required": True,
            },
            "id_nomenclature_sex": {
                "store": {
                    "type": "nomenclature",
                    "nomenclature_type": "SEXE",
                },
                "widget": {
                    "type": "nomenclature",
                    "attribut_label": "Sexe",
                },
            },
            "active": {
                "widget": {
                    "type": "bool_checkbox",
                    "attribut_label": "Actif",
                    "definition": "Activer cet individu",
                    "value": True,
                },
            },
            "comment": {"widget": {"type": "textarea", "attribut_label": "Commentaires"}},
            "cd_nom": {
                "store": {"type": "taxonomy"},
                "widget": {
                    "type": "taxonomy",
                    "attribut_label": "Espèce",
                    "id_list": "__MODULE.ID_LIST_TAXONOMY",
                    "hidden": "({value}) => '__MODULE.CD_NOM' !== 'None'",
                },
                "required": "({value}) => '__MODULE.CD_NOM' === 'None'",
            },
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {
                    "type": "text",
                    "attribut_label": "Numérisateur",
                    "hidden": True,
                },
                "required": True,
            },
            "medias": {
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_individuals",
                },
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
