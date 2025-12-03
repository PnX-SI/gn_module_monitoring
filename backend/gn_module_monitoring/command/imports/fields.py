from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert


from geonature.utils.env import DB
from geonature.core.imports.models import (
    BibFields,
    BibThemes,
)


def prepare_fields(specific_data, generic_data, entity_code, id_destination, parent_data):
    """
    Prépare les champs (fields) à insérer dans bib_fields à partir des données spécifiques et génériques.
    Organise les données sous deux clés : 'generic' et 'specific'.
    """
    entity_fields = {
        "generic": [],
        "specific": [],
        "label": specific_data.get("label", generic_data.get("label", entity_code)),
    }

    ignored_fields = [
        "id_module",  # handled manually
        "id_dataset",  # handled manually
        "id_digitiser",  # handled manually
        "uuid_base_visit",  # handled manually
        "uuid_base_site",  # handled manually
        "uuid_observation",  # handled manually
        "id_base_site",  # generated
        "id_base_visit",  # generated
        "id_observation",  # generated
        "last_visit",  # dynamic
        "nb_visits",  # dynamic
        "nb_observations",  # dynamic
        "medias",  # not importable
    ]

    field_set_manually = []

    generic_fields = generic_data.get("generic", {})
    for field_name, generic_field_data in generic_fields.items():
        field_data = {}
        if field_name in ignored_fields:
            continue

        elif field_name in specific_data.get("specific", {}):
            field_data = {**generic_field_data, **specific_data["specific"][field_name]}
            if field_name in field_set_manually:
                field_data["required"] = False
                field_data["display"] = False
            entity_fields["specific"].append(
                monitoring_field_to_bib_field(
                    field_data, entity_code, field_name, id_destination, generic_data, parent_data
                )
            )
        else:
            field_data = generic_field_data
            if field_name in field_set_manually:
                field_data["required"] = False
                field_data["display"] = False
            entity_fields["generic"].append(
                monitoring_field_to_bib_field(
                    field_data, entity_code, field_name, id_destination, generic_data, parent_data
                )
            )

    additional_fields = set(specific_data.get("specific", {}).keys()).difference(
        generic_fields.keys()
    )
    for field_name in additional_fields:
        if field_name in ignored_fields:
            continue
        field_data = specific_data["specific"][field_name]
        entity_fields["specific"].append(
            monitoring_field_to_bib_field(
                field_data, entity_code, field_name, id_destination, generic_data, parent_data
            )
        )

    return entity_fields


def determine_field_type(field_data: dict) -> str:
    """
    Détermine le type SQL du champ en fonction du widget et du type utilitaire.

    Parameters
    ----------
    field_data : dict
        Dictionnaire contenant la configuration du champ avec les clés:
        - type_widget: str, optionnel
            Type de widget (défaut: 'text')
        - type_util: str, optionnel
            Type utilitaire pour traitement spécial
        - multiple: bool, optionnel
            Si le champ permet plusieurs valeurs (défaut: False)
        - multi_select: bool, optionnel
            Drapeau alternatif pour valeurs multiples (défaut: False)

    Returns
    -------
    str
        Type SQL du champ en majuscules ('VARCHAR', 'INTEGER', etc.)
    """
    type_widget = field_data.get("type_widget", "text")
    type_util = field_data.get("type_util")
    multiple = field_data.get("multiple", field_data.get("multi_select", False))

    type_mapping = {
        "textarea": "text",
        "time": "varchar",
        "date": "date",
        "html": "varchar",
        "radio": "varchar",
        "select": "varchar",
        "medias": "varchar",
    }

    int_type_utils = ["user", "taxonomy", "nomenclature", "types_site", "module", "dataset"]

    if type_widget in ["observers", "datalist"]:
        return "integer[]" if multiple else "integer"

    if type_util in int_type_utils:
        return "integer"
    elif type_util in ["date", "uuid"]:
        return type_util

    if type_widget in ["checkbox", "multiselect"]:
        return "varchar[]"

    if type_widget in type_mapping:
        return type_mapping[type_widget].upper()

    if type_widget == "number":
        return "integer"

    if type_widget == "bool_checkbox":
        return "boolean"

    return "varchar"


def get_field_name(entity_code, field_name):
    if entity_code == "sites_group":
        return f"g__{field_name}"
    elif entity_code == "observation_detail":
        return f"d__{field_name}"
    return f"{entity_code[0]}__{field_name}"


def monitoring_field_to_bib_field(
    field_data, entity_code, field_name, id_destination: int, generic_data, parent_data
):
    """
    Crée un dictionnaire représentant un champ (field) à insérer dans bib_fields.
    """
    if "code_nomenclature_type" in field_data:
        mnemonique = field_data["code_nomenclature_type"]
    elif (
        "value" in field_data
        and isinstance(field_data["value"], dict)
        and "code_nomenclature_type" in field_data["value"]
    ):
        mnemonique = field_data["value"]["code_nomenclature_type"]
    else:
        mnemonique = None

    required_value = field_data.get("required", False)

    determined_type_field = determine_field_type(field_data)

    name_field = field_name
    parent_id_field_name = parent_data.get("id_field_name") if parent_data else None

    if name_field not in [generic_data.get("id_field_name"), parent_id_field_name]:
        name_field = get_field_name(entity_code, field_name)

    type_field_params = {
        k: v
        for k, v in field_data.items()
        if k not in ["required", "hidden", "type_widget", "attribut_label"]
    }

    return {
        "name_field": name_field,
        "fr_label": field_data.get("attribut_label", ""),
        "eng_label": None,
        "type_field": field_data.get("type_widget", None),
        "type_column": determined_type_field,
        "mandatory": True if isinstance(required_value, str) else bool(required_value),
        "autogenerated": False,
        "display": True,
        "mnemonique": mnemonique,
        "source_field": f"src_{name_field}",
        "dest_field": name_field,
        "multi": False,
        "id_destination": id_destination,
        "mandatory_conditions": None,
        "optional_conditions": None,
        "type_field_params": type_field_params if type_field_params else None,
    }


def insert_bib_field(protocol_data):
    """
    Insère ou met à jour les champs uniques dans `bib_fields`.
    """
    all_fields = []

    for entity_fields in protocol_data.values():
        for field_type in ["generic", "specific"]:
            all_fields.extend(entity_fields[field_type])

    def upsert_field(field):
        values = {**field}
        values.pop("type_column", None)
        if values.get("type_field_params", None) is None:
            values.pop("type_field_params", None)
        set_ = {
            "fr_label": field.get("fr_label"),
            "eng_label": field.get("eng_label"),
            "type_field": field.get("type_field"),
            "type_field_params": field.get("type_field_params", None),
            "mandatory": field.get("mandatory"),
            "autogenerated": field.get("autogenerated"),
            "display": field.get("display"),
            "mnemonique": field.get("mnemonique"),
            "source_field": field.get("source_field"),
            "dest_field": field.get("dest_field"),
            "multi": field.get("multi"),
            "mandatory_conditions": field.get("mandatory_conditions", None),
            "optional_conditions": field.get("optional_conditions", None),
        }
        if set_["type_field_params"] is None:
            del set_["type_field_params"]
        stmt = (
            pg_insert(BibFields)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["name_field", "id_destination"],
                set_=set_,
            )
        )
        DB.session.execute(stmt)

    # Since conditions are based on existing fields sometimes yet not inserted
    # we need to insert them first without conditions
    for field in all_fields:
        without_conditions = field.copy()
        without_conditions.update(
            {
                "mandatory_conditions": None,
                "optional_conditions": None,
            }
        )

        upsert_field(without_conditions)

    field_with_conditions = [
        field
        for field in all_fields
        if field.get("mandatory_conditions", None) or field.get("optional_conditions", None)
    ]
    for field in field_with_conditions:
        upsert_field(field)


def delete_bib_fields(fields):
    """
    Supprime les champs de la table bib_fields.
    """
    field_ids = [f["id_field"] for f in fields]
    DB.session.execute(delete(BibFields).where(BibFields.id_field.in_(field_ids)))
    DB.session.flush()


def has_field_changes(existing, new) -> bool:
    """
    Vérifie si un champ a été modifié en comparant les attributs pertinents.
    """
    relevant_attrs = [
        "fr_label",
        "eng_label",
        "type_field",
        "mandatory",
        "autogenerated",
        "display",
        "mnemonique",
        "source_field",
        "dest_field",
        "multi",
        "mandatory_conditions",
        "optional_conditions",
        "type_field_params",
    ]

    return any(existing.get(attr) != new.get(attr) for attr in relevant_attrs)


def get_themes_dict():
    """Récupère les thèmes depuis bib_themes"""
    themes = DB.session.execute(
        select(BibThemes.id_theme, BibThemes.name_theme).filter(
            BibThemes.name_theme.in_(["general_info", "additional_data"])
        )
    ).all()
    return {theme.name_theme: theme.id_theme for theme in themes}
