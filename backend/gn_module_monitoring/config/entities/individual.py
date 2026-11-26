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
        ],
        "display_list": ["individual_name", "uuid_individual", "active", "nb_sites"],
        "uuid_field_name": "uuid_individual",
        "fields": {
            "id_individual": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Id individual", "hidden": True},
            },
            "nb_sites": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Nombre de sites associés"},
            },
            "uuid_individual": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "individual_name": {
                "store": {"type": "string"},
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
                "store": {"type": "bool"},
                "widget": {
                    "type": "bool_checkbox",
                    "attribut_label": "Actif",
                    "definition": "Activer cet individu",
                    "value": True,
                },
            },
            "comment": {
                "store": {"type": "string"},
                "widget": {"type": "textarea", "attribut_label": "Commentaires"},
            },
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
                    "attribut_label": "Numérisateur",
                    "hidden": True,
                },
                "required": True,
            },
            "medias": {
                "store": {"type": "dummy"},
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
