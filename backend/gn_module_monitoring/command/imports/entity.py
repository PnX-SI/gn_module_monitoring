import re

import sqlalchemy as sa
from geonature.core.gn_permissions.models import PermObject
from geonature.core.imports.models import BibFields, Entity, EntityField
from geonature.utils.env import DB
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from gn_module_monitoring.command.imports.constant import (
    ENTITIES_NOT_AVAILABLE,
    TABLE_NAME_SUBMODULE,
    TOOLTIPS,
    UUID_FIELD_NAME,
)
from gn_module_monitoring.command.imports.fields import get_themes_dict
from gn_module_monitoring.config.utils import json_from_file, monitoring_module_config_path
from gn_module_monitoring.utils.utils import extract_keys


def get_entities_protocol(module_code: str) -> list:
    """
    Extrait les entités à partir du fichier de configuration pour un module donné.

    Parameters
    ----------
        module_code: str
            Code du module.

    Returns
    -------
        list
            Liste des entités du module.
    """
    module_path = monitoring_module_config_path(module_code)

    if not (module_path / "config.json").is_file():
        raise Exception(f"Le fichier config.json est manquant pour le module {module_code}")

    data_config = json_from_file(module_path / "config.json")
    tree = data_config.get("tree", {}).get("module", {})
    keys = extract_keys(tree)
    return [key for key in list(dict.fromkeys(keys)) if key not in ENTITIES_NOT_AVAILABLE]


def get_entity_parent(tree: dict, entity_code: str):
    """
    Trouve le parent d'une entité à l'aide de la configuration du protocole (`config.json`).
    """

    def find_parent(node, target, parent=None):
        if target in node:
            return parent
        for key, value in node.items():
            if isinstance(value, dict):
                found = find_parent(value, target, key)
                if found:
                    return found
        return None

    parent_entity = find_parent(tree, entity_code)
    return parent_entity


def insert_entities(
    unique_fields: dict, id_destination: int, entity_hierarchy_map: dict, module_code: str
):
    """
    Insère ou met à jour les entités dans `bib_entities` en respectant la hiérarchie des entités disponibles dans le
    fichier `config.json` du protocole.
    Les entités sont insérées/mises à jour en fonction de leur parent.

    Parameters
    ----------
        unique_fields: dict
            Dictionnaire des champs disponibles pour chaque entité.
        id_destination: int
            Identifiant de la destination.
        entity_hierarchy_map: dict
            Dictionnaire contenant la hiérarchie des entités.
        module_code: str
            Code du module.

    Returns
    -------
        dict
            Dictionnaire contenant les identifiants des entités insérées/mises à jour.
    """
    inserted_entity_ids = {}
    order = 1

    for entity_code in get_entities_protocol(module_code):
        entity_data = unique_fields[entity_code]
        entity_config = entity_hierarchy_map.get(entity_code)
        id_field_name = entity_config["id_field_name"]
        uuid_field_name = UUID_FIELD_NAME[entity_code]
        parent_entity = entity_config["parent_entity"]

        id_field = DB.session.scalar(
            sa.select(BibFields.id_field).filter_by(
                name_field=id_field_name, id_destination=id_destination
            )
        )

        uuid_field = DB.session.scalar(
            sa.select(BibFields.id_field).filter_by(
                name_field=uuid_field_name, id_destination=id_destination
            )
        )

        id_parent = inserted_entity_ids.get(parent_entity) if parent_entity else None

        entity_code_obs_detail = (
            "obs_detail" if entity_code == "observation_detail" else entity_code
        )
        mapping_entity_object_code = {
            "site": "MONITORINGS_SITES",
            "visit": "MONITORINGS_VISITES",
            "observation": "MONITORINGS_OBSERVATIONS",
        }
        id_object = DB.session.scalar(
            select(PermObject.id_object).filter_by(
                code_object=mapping_entity_object_code[entity_code]
            )
        )
        entity_data = {
            "id_destination": id_destination,
            "code": entity_code_obs_detail,
            "label": entity_data["label"][:64] if entity_data["label"] else entity_code,
            "order": order,
            "validity_column": f"{entity_code.lower()}_valid",
            "destination_table_schema": "gn_monitoring",
            "destination_table_name": TABLE_NAME_SUBMODULE.get(entity_code),
            "id_unique_column": id_field,
            "id_parent": id_parent,
            "id_object": id_object,
            "id_uuid_column": uuid_field,
        }

        order += 1

        existing_entity_id = DB.session.execute(
            select(Entity.id_entity).filter_by(
                code=entity_code_obs_detail, id_destination=id_destination
            )
        ).scalar()

        if existing_entity_id:
            DB.session.execute(
                update(Entity).where(Entity.id_entity == existing_entity_id).values(**entity_data)
            )
            inserted_entity_id = existing_entity_id
        else:
            result = DB.session.execute(pg_insert(Entity).values(**entity_data))
            DB.session.flush()

            inserted_entity_id = (
                result.inserted_primary_key[0] if result.inserted_primary_key else None
            )

            if not inserted_entity_id:
                inserted_entity_id = DB.session.scalar(
                    select(Entity.id_entity).filter_by(
                        code=entity_code_obs_detail, id_destination=id_destination
                    )
                )

        inserted_entity_ids[entity_code] = inserted_entity_id
        DB.session.flush()


def get_entity_ids_dict(protocol_data: dict, id_destination: int):
    """
    Récupère les IDs des entités depuis `bib_entities`

    Parameters
    ----------
    protocol_data : dict
        Dictionnaire contenant la config du protocole
    id_destination : int
        ID de la destination (table) où chercher les IDs des entités

    Returns
    -------
    dict
        Dictionnaire contenant les IDs des entités correspondant aux codes des entités passés en paramètre
    """
    entity_code_map = {"observation_detail": "obs_detail"}
    return {
        entity_code: DB.session.execute(
            select(Entity.id_entity).filter_by(
                code=entity_code_map.get(entity_code, entity_code), id_destination=id_destination
            )
        ).scalar()
        for entity_code in protocol_data.keys()
    }


def insert_entity_field_relations(
    protocol_data: dict, id_destination: int, entity_hierarchy_map: dict
):
    """
    Insère les relations entre les entités et les champs dans cor_entity_field

    Parameters
    ----------
    protocol_data : dict
        Dictionnaire contenant la config du protocole
    id_destination : int
        ID de la destination (table) où chercher les IDs des entités
    entity_hierarchy_map : dict
        Dictionnaire contenant la hiérarchie des entités

    Returns
    -------
    None
    """
    bib_themes = get_themes_dict()
    entity_ids = get_entity_ids_dict(protocol_data, id_destination)
    for entity_code, fields in protocol_data.items():
        entity_id = entity_ids.get(entity_code)
        display_properties = protocol_data[entity_code].get("display_properties", [])
        # raise Exception("stop")
        max_order = len(display_properties) + 1
        for field_type in ["generic", "specific"]:
            for field in fields[field_type]:
                field_name = re.sub(r"^[a-z]__", "", field["name_field"])
                order = (
                    display_properties.index(field_name) + 1
                    if field_name in display_properties
                    else max_order
                )
                if get_cor_entity_field(
                    entity_id=entity_id,
                    field_name=field["name_field"],
                    id_destination=id_destination,
                    bib_themes=bib_themes,
                    order=order,
                ):
                    max_order += 1

        parent_code = entity_hierarchy_map[entity_code]["parent_entity"]
        if parent_code:
            get_cor_entity_field(
                entity_id=entity_id,
                field_name=entity_hierarchy_map[parent_code]["id_field_name"],
                id_destination=id_destination,
                bib_themes=bib_themes,
                is_parent_link=True,
            )
            get_cor_entity_field(
                entity_id=entity_id,
                field_name=f"uuid_base_{parent_code}",
                id_destination=id_destination,
                bib_themes=bib_themes,
                is_parent_link=True,
            )
            get_cor_entity_field(
                entity_id=entity_id,
                field_name=f"id_base_{parent_code}_origin",
                id_destination=id_destination,
                bib_themes=bib_themes,
                is_parent_link=True,
            )


def get_cor_entity_field(
    entity_id, field_name, id_destination, bib_themes, order=None, is_parent_link=False
):
    """
    Crée une relation entre une entité et un champ dans cor_entity_field.

    Parameters
    ----------
    entity_id : int
        ID de l'entité
    field_name : str
        Nom du champ
    id_destination : int
        ID de la destination (table) où chercher les IDs des entités
    bib_themes : dict
        Dictionnaire contenant les thèmes
    order : int
        Ordre du champ dans la hiérarchie des entités
    is_parent_link : bool
        Indique si le champ est une relation parent

    Returns
    -------
    bool
        True si la relation a été créée, False sinon
    """

    id_field = DB.session.execute(
        select(BibFields.id_field).filter_by(name_field=field_name, id_destination=id_destination)
    ).scalar_one()

    if DB.session.execute(
        sa.exists()
        .where(EntityField.id_entity == entity_id, EntityField.id_field == id_field)
        .select()
    ).scalar():
        return False

    data = {
        "id_entity": entity_id,
        "id_field": id_field,
        "id_theme": bib_themes["general_info"],
        "order_field": 0 if is_parent_link else (order or 1),
        "desc_field": "",
        "comment": TOOLTIPS.get(field_name, None),
    }

    stmt = (
        pg_insert(EntityField)
        .values(**data)
        .on_conflict_do_update(
            index_elements=["id_entity", "id_field"],
            set_={
                "order_field": data["order_field"],
                "desc_field": data["desc_field"],
                "comment": data["comment"],
            },
        )
    )

    DB.session.execute(stmt)
    DB.session.flush()
    return True


def update_entity_label(destination_id: int, new_label: str):
    """
    Met à jour tous les libellés des entités associées à une même destination dans la table `Entity`.

    Parameters
    ----------

        destination_id: int
            ID de la destination associée.
        new_label: str
            Nouveau libellé à appliquer à toutes les entités.
    """
    entities = (
        DB.session.execute(select(Entity).filter_by(id_destination=destination_id)).scalars().all()
    )
    for entity in entities:
        if entity.label != new_label:
            entity.label = new_label
            DB.session.add(entity)
    print(entity.label == new_label)
    print(f"Libellé de l'entité mis à jour : '{entity.label}' -> '{new_label}'")
    DB.session.flush()
