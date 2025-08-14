from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
import sqlalchemy as sa


from geonature.utils.env import DB
from geonature.core.gn_permissions.models import (
    PermObject,
)
from geonature.core.imports.models import (
    BibFields,
    Entity,
    EntityField,
)


from gn_module_monitoring.config.utils import (
    json_from_file,
    monitoring_module_config_path,
)
from gn_module_monitoring.command.imports.constant import TABLE_NAME_SUBMODULE, UUID_FIELD_NAME
from gn_module_monitoring.command.imports.fields import get_themes_dict
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
    unique_keys = list(dict.fromkeys(keys))
    if "sites_group" in unique_keys:
        unique_keys.remove(
            "sites_group"
        )  # sites_group are not available for import at the moment.
    return unique_keys


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
    unique_fields, id_destination: int, entity_hierarchy_map: dict, module_code: str
):
    """
    Insère ou met à jour les entités dans bib_entities en respectant la hiérarchie du tree.
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
            "id_uuid_column":uuid_field
        }

        order += 1

        existing_entity = DB.session.execute(
            select(Entity.id_entity).filter_by(
                code=entity_code_obs_detail, id_destination=id_destination
            )
        ).scalar()

        if existing_entity:
            DB.session.execute(
                update(Entity).where(Entity.id_entity == existing_entity).values(**entity_data)
            )
            inserted_entity_id = existing_entity
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
    Récupère les IDs des entités depuis bib_entities
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


def insert_entity_field_relations(protocol_data, id_destination, entity_hierarchy_map):
    """
    Insère les relations entre les entités et les champs dans cor_entity_field
    """
    bib_themes = get_themes_dict()
    entity_ids = get_entity_ids_dict(protocol_data, id_destination)

    for entity_code, fields in protocol_data.items():
        entity_id = entity_ids.get(entity_code)
        order = 1
        for field_type in ["generic", "specific"]:
            for field in fields[field_type]:
                if get_cor_entity_field(
                    entity_id=entity_id,
                    field_name=field["name_field"],
                    id_destination=id_destination,
                    bib_themes=bib_themes,
                    order=order,
                ):
                    order += 1

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


def get_cor_entity_field(
    entity_id, field_name, id_destination, bib_themes, order=None, is_parent_link=False
):
    """
    Crée une relation entre une entité et un champ dans cor_entity_field
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
        "comment": None,
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
