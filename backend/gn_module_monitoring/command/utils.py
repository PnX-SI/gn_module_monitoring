import os
import subprocess
import json
from pathlib import Path

from flask import current_app
from sqlalchemy import and_, text, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from geonature.utils.env import DB
from geonature.core.gn_permissions.models import (
    PermObject,
    PermissionAvailable,
    PermAction,
    cor_object_module,
)
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.imports.models import BibFields
from geonature.core.imports.models import Destination
from geonature.core.imports.models import Entity
from geonature.core.imports.models import EntityField
from geonature.core.imports.models import BibThemes
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.config.utils import (
    json_from_file,
    monitoring_module_config_path,
    map_field_type,
    SUB_MODULE_CONFIG_DIR,
    DATABASE_URI
)

from gn_module_monitoring.config.repositories import get_config

from gn_module_monitoring.modules.repositories import get_module, get_source_by_code, get_modules


"""
utils.py

fonctions pour les commandes du module monitoring
"""


FORBIDDEN_SQL_INSTRUCTION = [
    "INSERT ",
    "DELETE ",
    "UPDATE ",
    "EXECUTE ",
    "TRUNCATE ",
    "ALTER ",
    "GRANT ",
    "COPY ",
    "PERFORM ",
    "CASCADE",
]

PERMISSION_LABEL = {
    "MONITORINGS_MODULES": {"label": "modules", "actions": ["R", "U", "E"]},
    "MONITORINGS_GRP_SITES": {"label": "groupes de sites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_SITES": {"label": "sites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_VISITES": {"label": "visites", "actions": ["C", "R", "U", "D"]},
}

ACTION_LABEL = {
    "C": "Créer des",
    "R": "Voir les",
    "U": "Modifier les",
    "D": "Supprimer des",
    "E": "Exporter les",
}

TABLE_NAME_SUBMODULDE = {
    "sites_group": "t_sites_groups",
    "site": "t_base_sites",
    "visit": "t_base_visits",
    "observation": "t_observations",
}

TYPE_WIDGET = {
    "select": "varchar",
    "checkbox": "varchar[]",
    "radio": "varchar",
    "html": "text",
    "bool_checkbox": "boolean",
    "number": "integer",
    "multiselect": "varchar[]",
    "observers": "integer[]", 
    "media": "varchar",
    "date": "date",
    "nomenclature": "integer",
    "datalist": "integer",
    "text": "varchar",
    "textarea": "text", 
    "integer": "integer",
    "jsonb": "jsonb",
    "time": "varchar",
    "taxonomy": "integer",
}

def process_sql_files(
    dir=None, module_code=None, depth=1, allowed_files=["export.sql", "synthese.sql"]
):
    sql_dir = Path(monitoring_module_config_path(module_code))
    if dir:
        sql_dir = sql_dir / "exports/csv"
    if not sql_dir.is_dir():
        return

    if not allowed_files:
        allowed_files = []
    count_depth = 0
    for root, dirs, files in os.walk(sql_dir, followlinks=True):
        count_depth = count_depth + 1
        for f in files:
            if not f.endswith(".sql"):
                continue
            if not f in allowed_files and allowed_files:
                continue
            # Vérification commandes non autorisée
            try:
                execute_sql_file(root, f, module_code, FORBIDDEN_SQL_INSTRUCTION)
                print("{} - exécution du fichier : {}".format(module_code, f))
            except Exception as e:
                print(e)

        # Limite profondeur de la recherche dans les répertoires
        if depth:
            if count_depth >= depth:
                break


def execute_sql_file(dir, file, module_code, forbidden_instruction=[]):
    """
    Execution d'un fichier sql dans la base de donnée
    dir : nom du répertoire
    file : nom du fichier à éxécuter
    module_code : code du module
    forbidden_instruction : liste d'instructions sql qui sont proscrites du fichier.

    """
    sql_content = Path(Path(dir) / file).read_text()
    for sql_cmd in forbidden_instruction:
        if sql_cmd.lower() in sql_content.lower():
            raise Exception(
                "erreur dans le script {} instruction sql non autorisée {}".format(
                    module_code, file, sql_cmd
                )
            )

    try:
        DB.engine.execute(
            text(sql_content),
            module_code=module_code,
        )
    except Exception as e:
        raise Exception("{} - erreur dans le script {} : {}".format(module_code, file, e))


def process_available_permissions(module_code, session):
    try:
        module = get_module("module_code", module_code)
    except Exception:
        print("le module n'existe pas")
        return

    config = get_config(module_code, force=True)
    if not config:
        print(f"Il y a un problème de configuration pour le module {module_code}")
        return

    tree = config.get("tree", [])

    module_objects = [k for k in extract_keys(tree, keys=[])]

    permission_level = current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})

    # Insert permission object
    for permission_object_code in module_objects:
        print(f"Création des permissions pour {module_code} : {permission_object_code}")
        insert_module_available_permissions(
            module_code, permission_level[permission_object_code], session=session
        )


def insert_module_available_permissions(module_code, perm_object_code, session):
    object_label = PERMISSION_LABEL.get(perm_object_code)["label"]

    if not object_label:
        print(f"L'object {perm_object_code} n'est pas traité")

    try:
        module = session.scalars(select(TModules).where(TModules.module_code == module_code)).one()
    except NoResultFound:
        print(f"Le module {module_code} n'est pas présent")
        return

    try:
        perm_object = session.execute(
            select(PermObject).where(PermObject.code_object == perm_object_code)
        ).scalar_one_or_none()
    except NoResultFound:
        print(f"L'object de permission {perm_object_code} n'est pas présent")
        return

    stmt = (
        pg_insert(cor_object_module)
        .values(id_module=module.id_module, id_object=perm_object.id_object)
        .on_conflict_do_nothing()
    )
    session.execute(stmt)
    session.commit()

    # Création d'une permission disponible pour chaque action
    object_actions = PERMISSION_LABEL.get(perm_object_code)["actions"]
    for action in object_actions:
        permaction = session.execute(
            select(PermAction).where(PermAction.code_action == action)
        ).scalar_one()
        try:
            perm = session.execute(
                select(PermissionAvailable).where(
                    PermissionAvailable.module == module,
                    PermissionAvailable.object == perm_object,
                    PermissionAvailable.action == permaction,
                )
            ).scalar_one()
        except NoResultFound:
            label = f"{ACTION_LABEL[action]} {object_label}"
            if action == "E" and perm_object.code_object == "MONITORINGS_MODULES":
                label = "Export les données du module"
            perm = PermissionAvailable(
                module=module,
                object=perm_object,
                action=permaction,
                label=label,
                scope_filter=True,
            )
            session.add(perm)


def remove_monitoring_module(module_code):
    try:
        module = get_module("module_code", module_code)
    except Exception:
        print("le module n'existe pas")
        return

    # remove module in db
    try:
        # suppression des permissions disponibles pour ce module
        # txt = f"DELETE FROM gn_permissions.t_permissions_available WHERE id_module = {module.id_module}"
        stmt = delete(PermissionAvailable).where(PermissionAvailable.id_module == module.id_module)

        DB.session.execute(stmt)

        stmt = delete(Destination).where(Destination.code == module_code)
        DB.session.execute(stmt)
        
        stmt = delete(TModules).where(TModules.id_module == module.id_module)
        DB.session.execute(stmt)
        DB.session.commit()
    except IntegrityError:
        print("Impossible de supprimer le module car il y a des données associées")
        return
    except Exception as e:
        print("Impossible de supprimer le module")
        raise (e)

    # suppression source pour la synthese
    try:
        print("Remove source {}".format("MONITORING_" + module_code.upper()))
        source = get_source_by_code("MONITORING_" + module_code.upper())
        DB.session.delete(source)
        DB.session.commit()
    except Exception as e:
        print("Impossible de supprimer la source {}".format(str(e)))
        # return
    # run specific sql TODO
    # remove nomenclature TODO
    return


def add_nomenclature(module_code):
    path_nomenclature = monitoring_module_config_path(module_code) / "nomenclature.json"

    if not path_nomenclature.is_file():
        print("Il n'y a pas de nomenclature à insérer pour ce module")
        return

    nomenclature = json_from_file(path_nomenclature, None)
    if not nomenclature:
        print("Il y a un problème avec le fichier {}".format(path_nomenclature))
        return

    for data in nomenclature.get("types", []):
        nomenclature_type = DB.session.execute(
            select(BibNomenclaturesTypes).where(
                data.get("mnemonique") == BibNomenclaturesTypes.mnemonique
            )
        ).scalar_one_or_none()

        if nomenclature_type:
            action = "already exist"
            print(
                "nomenclature type {} - {} - {}".format(
                    nomenclature_type.mnemonique, nomenclature_type.label_default, action
                )
            )

            continue

        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"

        nomenclature_type = BibNomenclaturesTypes(**data)
        DB.session.add(nomenclature_type)
        DB.session.commit()
        action = "added"
        print(
            "nomenclature type {} - {} - {}".format(
                nomenclature_type.mnemonique, nomenclature_type.label_default, action
            )
        )

    for data in nomenclature["nomenclatures"]:
        insert_update_nomenclature(data)


def insert_update_nomenclature(data):

    # Get Id type
    id_type = DB.session.execute(
        select(BibNomenclaturesTypes.id_type).where(
            BibNomenclaturesTypes.mnemonique == data["type"]
        )
    ).scalar_one_or_none()

    if not id_type:
        print(
            'probleme de type avec mnemonique="{}" pour la nomenclature {}'.format(
                data["type"], data
            )
        )
        return

    # Get nomenclature if exist
    action = "updated"
    nomenclature = DB.session.execute(
        select(TNomenclatures)
        .join(BibNomenclaturesTypes, BibNomenclaturesTypes.id_type == TNomenclatures.id_type)
        .where(
            and_(
                data.get("cd_nomenclature") == TNomenclatures.cd_nomenclature,
                data.get("type") == BibNomenclaturesTypes.mnemonique,
            )
        )
    ).scalar_one_or_none()

    # If not create new one
    if not nomenclature:
        nomenclature = TNomenclatures()
        action = "added"

    data["label_fr"] = data.get("label_fr") or data["label_default"]
    data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
    data["source"] = data.get("source") or "monitoring"
    data["statut"] = data.get("statut") or "Validation en cours"
    data["active"] = True
    data["id_type"] = id_type

    for key, value in data.items():
        if hasattr(nomenclature, key):
            setattr(nomenclature, key, value)

    DB.session.add(nomenclature)
    DB.session.commit()
    if data["type"] == "TYPE_SITE":
        existing_bib_type_site = DB.session.get(BibTypeSite, nomenclature.id_nomenclature)
        if not existing_bib_type_site:
            bib_type_site = BibTypeSite(id_nomenclature_type_site=nomenclature.id_nomenclature)
            DB.session.add(bib_type_site)
            DB.session.commit()

    print(
        "nomenclature {} - {} - {}".format(
            nomenclature.cd_nomenclature, nomenclature.label_default, action
        )
    )


def installed_modules(session=None):
    return [
        {
            "module_code": module.module_code,
            "module_label": module.module_label,
            "module_desc": module.module_desc,
        }
        for module in get_modules(session)
    ]


def available_modules():
    """
    renvoie la liste des modules disponibles non encore installés
    """
    installed_module_codes = list(map(lambda x: x["module_code"], installed_modules()))
    available_modules_ = []
    for root, dirs, files in os.walk(SUB_MODULE_CONFIG_DIR, followlinks=True):
        for d in dirs:
            module_file = Path(root) / d / "module.json"
            if d in installed_module_codes or not module_file.exists():
                continue
            module = json_from_file(module_file)
            available_modules_.append({**module, "module_code": d})
        break
    return available_modules_


def extract_keys(test_dict, keys=[]):
    """
    Fonction permettant d'extraire de façon récursive les clés d'un dictionnaire.
    """
    for key, val in test_dict.items():
        keys.append(key)
        if isinstance(val, dict):
            extract_keys(val, keys)
    return keys

def get_entities_protocol(module_code: str) -> list:
    """
    Extrait les entités à partir du fichier de configuration pour un module donné.
    
    Args:
        module_code (str): Code du module.
    
    Returns:
        list: Liste des entités du module.
    """
    module_path = monitoring_module_config_path(module_code)

    if not (module_path / "config.json").is_file():
        raise Exception(f"Le fichier config.json est manquant pour le module {module_code}")

    data_config = json_from_file(module_path / "config.json")
    tree = data_config.get("tree", {}).get("module", {})
    keys = extract_keys(tree)
    unique_keys = list(dict.fromkeys(keys))

    return unique_keys

def get_entity_parent(tree, entity_code):
    """
    Trouve le parent d'une entité dans la structure de l'arbre.
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

def process_module_import(module_data):
    """
    Pipeline complet pour insérer un protocole et ses données dans la base.
    
    Args:
        module_data (dict): Données de la table gn_commons.t_modules du module à importer.
    """
    try:
        destination = upsert_bib_destination(module_data)
        id_destination = destination.id_destination
        module_code = module_data["module_code"]

        entities = get_entities_protocol(module_code)
        protocol_data, entity_column_map = build_protocol_json(entities, module_code, id_destination)

        sql = create_import_table(module_code,protocol_data)
        
        create_import_table_protocol(module_code,sql)
        
        insert_unique_fields(protocol_data)
        
        insert_entities(protocol_data, id_destination, entity_column_map, label_entity=destination.label)

        insert_entity_field_relations(protocol_data, id_destination, entity_column_map)

    except Exception as e:
        print(f"Erreur lors du traitement du module {module_data['module_code']}: {str(e)}")
        raise


def upsert_bib_destination(module_data: dict) -> Destination:
    """
    Ajoute ou met à jour une destination dans bib_destinations.
    
    Args:
        module_data (dict): Données de la table gn_commons.t_modules du module à importer.
    
    Returns:
        Destination: L'objet Destination inséré ou mis à jour.
    """
    existing_destination = (
        DB.session.query(Destination).filter_by(code=module_data["module_code"]).one_or_none()
    )

    if existing_destination:
        print(f"La destination pour {module_data['module_code']} existe déjà, mise à jour.")
        existing_destination.label = module_data["module_label"]
        existing_destination.table_name = f"t_import_{module_data['module_code'].lower()}"
        DB.session.commit()
        return existing_destination

    module_monitoring_code = DB.session.query(TModules).filter_by(module_code=module_data["module_code"]).one()
    destination_data = {
        "id_module": module_monitoring_code.id_module,
        "code": module_data["module_code"],
        "label": module_data["module_label"],
        "table_name": f"t_import_{module_data['module_code'].lower()}",
    }
    destination = Destination()
    destination.from_dict(destination_data)
    DB.session.add(destination)
    DB.session.commit()
    return destination


def build_protocol_json(entities: list, module_code: str, id_destination: int):
    """
    Construit les données du protocole à partir des fichiers JSON spécifiques et génériques.
    
    Args:
        entities (list): Liste des entités du module.
        module_code (str): Code du module.
        id_destination (int): ID de la destination dans bib_destinations.
    
    Returns:
        Données du protocole et mapping des colonnes des entités.
    """
    protocol_data = {}
    entity_column_map = {}
    module_config_dir_path = monitoring_module_config_path(module_code)

    module_config_path = module_config_dir_path / "config.json"
    if not module_config_path.is_file():
        raise Exception(f"Le fichier config.json est manquant pour le module {module_code}")

    module_config = json_from_file(module_config_path)
    tree = module_config.get("tree", {}).get("module", {})

    for entity_code in entities:
        file_path = module_config_dir_path / f"{entity_code}.json"
        if not file_path.is_file():
            raise Exception(f"Le fichier {entity_code}.json est manquant")

        specific_data = json_from_file(file_path)
        if not specific_data:
            raise Exception(f"Le fichier {entity_code}.json est vide")

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        generic_data_path = os.path.join(project_root, "config", "generic", f"{entity_code}.json")
        generic_data = json_from_file(generic_data_path, result_default={})
        if not generic_data:
            raise Exception(f"Le fichier generic/{entity_code}.json est vide")

        parent_entity = get_entity_parent(tree, entity_code)
        uuid_column = generic_data.get( "id_field_name")

        entity_column_map[entity_code] = {
            "uuid_column": uuid_column,
            "parent_entity": parent_entity
        }

        protocol_data[entity_code] = prepare_fields(specific_data, generic_data, entity_code, id_destination)

    return protocol_data, entity_column_map


def prepare_fields(specific_data, generic_data, entity_code, id_destination):
    """
    Prépare les champs (fields) à insérer dans bib_fields à partir des données spécifiques et génériques.
    Gère également un champ additionnel consolidé (`additional_data`).
    """
    fields = []
    specific_fields = specific_data.get("specific", {})
    generic_fields = generic_data.get("generic", {})

    mandatory_conditions = []
    optional_conditions = []


    for field_name, generic_field_data in generic_fields.items():

        if field_name in specific_fields:
            field_data = {**generic_field_data, **specific_fields[field_name]}
        else:
            field_data = generic_field_data

        fields.append(create_bib_field(field_data, entity_code, field_name, id_destination, json.dumps(field_data)))

    additional_fields = set(specific_fields.keys()).difference(generic_fields.keys())
    for field_name in additional_fields:
        field_data = specific_fields[field_name]

        fields.append(create_bib_field(field_data, entity_code, field_name, id_destination, json.dumps(field_data)))

        if field_data.get("required", False): 
            mandatory_conditions.append(f"{entity_code[0]}__{field_name}")
        else: 
            optional_conditions.append(f"{entity_code[0]}__{field_name}")

    if additional_fields:
        fields.append(create_bib_field(
            {
                "attribut_label": "Champs additionnels",
                "type_widget": "jsonb",
                "required": bool(mandatory_conditions),
                "hidden": False,
            },
            entity_code=entity_code,
            field_name="additional_data",
            id_destination=id_destination,
            type_field=json.dumps({}),
            is_additional=True,
            multi=True,
            mandatory=mandatory_conditions,
            optional=optional_conditions
        ))


    return fields

def determine_field_type(field_data):
    """
    Détermine le type de colonne PostgreSQL en fonction du type_widget, type_util et paramètres multiples.
    
    Args:
        field_data (dict): Données du champ
    
    Returns:
        str: Type de colonne PostgreSQL
    """
    type_widget = field_data.get('type_widget', 'text')
    type_util = field_data.get('type_util')
    multiple = field_data.get('multiple', field_data.get('multi_select', False))

    type_mapping = {
        'textarea': 'text',
        'time': 'varchar',
        'date': 'varchar',
        'html': 'varchar',
        'radio': 'varchar',
        'select': 'varchar',
        'medias': 'varchar',
    }

    int_type_utils = ['user', 'taxonomy', 'nomenclature', 'types_site', 'module', 'dataset']

    if type_widget in ['observers', 'datalist']:
        return 'INTEGER[]' if multiple else 'INTEGER'

    if type_util in int_type_utils:
        return 'INTEGER'

    if type_widget in ['checkbox', 'multiselect']:
        return 'VARCHAR[]'

    if type_widget in type_mapping:
        return type_mapping[type_widget].upper()

    if type_widget == 'number':
        return 'INTEGER'

    if type_widget == 'bool_checkbox':
        return 'BOOLEAN'

    return 'VARCHAR'

def create_bib_field(
    field_data, 
    entity_code, 
    field_name, 
    id_destination: int, 
    type_field=None,
    is_additional=False, 
    mnemonique=None, 
    multi=None, 
    mandatory=None, 
    optional=None
):
    """
    Crée un dictionnaire représentant un champ (field) à insérer dans bib_fields.
    """
    if mnemonique is None:
        if "code_nomenclature_type" in field_data:
            mnemonique = field_data["code_nomenclature_type"]
        elif "value" in field_data and isinstance(field_data["value"], dict) and "code_nomenclature_type" in field_data["value"]:
            mnemonique = field_data["value"]["code_nomenclature_type"]

    required_value = field_data.get("required", False)
    hidden_value = field_data.get("hidden", False)

    determined_type_field = determine_field_type(field_data)

    return {
        "name_field": f"{entity_code[0]}__{field_name}",
        "fr_label": field_data.get("attribut_label", ""),
        "eng_label": None,
        "type_field": determined_type_field,
        "mandatory": True if isinstance(required_value, str) else bool(required_value),
        "autogenerated": False,
        "display": not (True if isinstance(hidden_value, str) else bool(hidden_value)),
        "mnemonique": mnemonique,
        "source_field": f"src_{field_name}",
        "dest_field": field_name,
        "multi": multi if multi is not None else False,
        "id_destination": id_destination,
        "mandatory_conditions": field_data.get("mandatory_conditions", []),
        "optional_conditions": field_data.get("optional_conditions", []),
        "type_field_params": field_data.get("type_field_params", {}),
    }

def insert_unique_fields(protocol_data):
    """
    Insère ou met à jour les champs uniques dans `BibFields`.
g    """
    all_fields = []
    additional_fields = []

    for entity_fields in protocol_data.values():
        for field in entity_fields:
            if field["dest_field"].endswith("additional_data"):
                additional_fields.append(field)
            else:
                all_fields.append(field)

    def upsert_field(field):
        stmt = pg_insert(BibFields).values(**field).on_conflict_do_update(
            index_elements=["name_field", "id_destination"],
            set_={
                "fr_label": field.get("fr_label"),
                "eng_label": field.get("eng_label"),
                "type_field": field.get("type_field"),
                "mandatory": field.get("mandatory"),
                "autogenerated": field.get("autogenerated"),
                "display": field.get("display"),
                "mnemonique": field.get("mnemonique"),
                "source_field": field.get("source_field"),
                "dest_field": field.get("dest_field"),
                "multi": field.get("multi"),
                "mandatory_conditions": field.get("mandatory_conditions"),
                "optional_conditions": field.get("optional_conditions"),
            },
        )
        DB.session.execute(stmt)

    for field in all_fields + additional_fields:
        upsert_field(field)

    DB.session.commit()


def insert_entities(unique_fields, id_destination, entity_column_map, label_entity=None):
    """
    Insère ou met à jour les entités dans bib_entities en respectant la hiérarchie du tree.
    Si 'label_entity' est fourni, il contient les labels des entités.
    """
    inserted_entities = {}
    order = 1
    for entity_code, fields in unique_fields.items():

        entity_config = entity_column_map.get(entity_code)
        if not entity_config:
            raise Exception(f"Aucune configuration trouvée pour l'entité {entity_code}")

        uuid_column = entity_config["uuid_column"]
        parent_entity = entity_config["parent_entity"]

        uuid_field = next((f for f in fields if f["dest_field"] == uuid_column), None)
        if not uuid_field:
            raise Exception(f"Champ UUID '{uuid_column}' non trouvé pour l'entité {entity_code}")

        id_field = (
            DB.session.query(BibFields.id_field)
            .filter_by(name_field=uuid_field["name_field"], id_destination=id_destination)
            .scalar()
        )
        if not id_field:
            raise Exception(f"Champ UUID introuvable pour l'entité {entity_code} avec '{uuid_field['name_field']}'")

        id_parent = None
        if parent_entity:
            id_parent = inserted_entities.get(parent_entity)
            if not id_parent:
                raise Exception(f"L'entité parente '{parent_entity}' n'a pas été insérée pour '{entity_code}'")

        entity_data = {
            "id_destination": id_destination,
            "code": entity_code,
            "label": label_entity,
            "order": order,
            "validity_column": f"{entity_code.lower()}_valid",
            "destination_table_schema": "gn_monitoring",
            "destination_table_name": TABLE_NAME_SUBMODULDE.get(entity_code),
            "id_unique_column": id_field,
            "id_parent": id_parent,
        }

        order += 1
        stmt = pg_insert(Entity).values(**entity_data).on_conflict_do_nothing()
        result = DB.session.execute(stmt)

        inserted_entity_id = result.inserted_primary_key[0] if result.inserted_primary_key else None
        if not inserted_entity_id:
            inserted_entity_id = (
                DB.session.query(Entity.id_entity)
                .filter_by(code=entity_code, id_destination=id_destination)
                .scalar()
            )
        inserted_entities[entity_code] = inserted_entity_id

    DB.session.commit()


def insert_entity_field_relations(protocol_data, id_destination, entity_column_map):
    """
    Insère les relations dans cor_entity_field pour les entités et leurs champs,
    ainsi que les relations parent-enfant selon `entity_column_map`.
    """
    themes = DB.session.query(BibThemes.id_theme, BibThemes.name_theme).filter(BibThemes.name_theme.in_(["general_info", "additional_data"])).all()
    bib_themes = {theme.name_theme: theme.id_theme for theme in themes}
    
    entity_ids = {
        entity_code: DB.session.query(Entity.id_entity)
        .filter_by(code=entity_code, id_destination=id_destination)
        .scalar()
        for entity_code in protocol_data.keys()
    }

    for entity_code, fields in protocol_data.items():
        entity_id = entity_ids.get(entity_code)
        if not entity_id:
            raise Exception(f"Entité introuvable pour {entity_code}")

        order = 1
        for field in fields:
            id_field = (
                DB.session.query(BibFields.id_field)
                .filter_by(name_field=field["name_field"], id_destination=id_destination)
                .scalar()
            )
            if not id_field:
                raise Exception(f"Champ introuvable pour {field['name_field']}")

            existing_relation = (
                DB.session.query(EntityField)
                .filter_by(id_entity=entity_id, id_field=id_field)
                .one_or_none()
            )
            if not existing_relation:
                bib_theme = (
                    bib_themes["additional_data"] 
                    if field["name_field"].endswith("additional_data") 
                    else bib_themes["general_info"]
                )
                
                relation_data = create_relation_dict(
                    id_entity=entity_id, 
                    id_field=id_field, 
                    bib_theme=bib_theme,
                    order_field=order,
                    relation_type="additional_data" if field["name_field"].endswith("additional_data") else "field"
                )
                
                new_relation = EntityField()
                new_relation.from_dict(relation_data)
                DB.session.add(new_relation)
                order += 1

        parent_entity_code = entity_column_map.get(entity_code, {}).get("parent_entity")
        if parent_entity_code:
            parent_uuid_column = entity_column_map[parent_entity_code]["uuid_column"]
            parent_id_field = (
                DB.session.query(BibFields.id_field)
                .filter_by(name_field=f"{parent_entity_code[0]}__{parent_uuid_column}", id_destination=id_destination)
                .scalar()
            )

            if not parent_id_field:
                raise Exception(f"Champ UUID introuvable pour le parent {parent_entity_code}")

            parent_id = (
                DB.session.query(Entity.id_entity)
                .filter_by(code=parent_entity_code, id_unique_column=parent_id_field, id_destination=id_destination)
                .scalar()
            )

            if not parent_id:
                raise Exception(f"Parent introuvable pour {entity_code} (parent : {parent_entity_code})")

            existing_parent_relation = (
                DB.session.query(EntityField)
                .filter_by(id_entity=parent_id, id_field=entity_id)
                .one_or_none()
            )
            if parent_entity_code:
                parent_relation_data = create_relation_dict(
                    id_entity=entity_id,
                    id_field=parent_id_field,
                    bib_theme=bib_themes["general_info"],
                    relation_type="parent_child",
                    comment=f"{parent_entity_code} -> {entity_code}"
                )
                
                new_parent_relation = EntityField()
                new_parent_relation.from_dict(parent_relation_data)
                DB.session.add(new_parent_relation)

                DB.session.commit()
    
def create_relation_dict(
    id_entity, 
    id_field, 
    bib_theme, 
    order_field=1, 
    desc_field="", 
    comment=None,
    relation_type="field"
):
    """
    Crée un dictionnaire de relation standardisé.
    
    Returns:
        dict: Dictionnaire de configuration de relation
    """
    relation_dict = {
        "id_entity": id_entity,
        "id_field": id_field,
        "desc_field": desc_field,
        "id_theme": bib_theme,
        "order_field": order_field,
        "comment": comment,
    }
    
    if relation_type == "additional_data":
        relation_dict.update({
            "comment": "Attributs additionnels"
        })
    elif relation_type == "parent_child":
        relation_dict.update({
            "desc_field": f"Relation vers {comment}",
            "order_field": 0,
            "comment": f"Relation parent -> enfant ({comment})"
        })
    
    return relation_dict

def create_import_table(module_code: str, protocol_data) -> str:
    """
    Génère une requête SQL pour créer une table d'importation dynamique en fonction du module et des protocol_data.
    """
    table_name = f"gn_imports.t_import_{module_code.lower()}"
    
    base_columns = [
        "id_import INTEGER NOT NULL REFERENCES gn_imports.t_imports ON UPDATE CASCADE ON DELETE CASCADE",
        "line_no INTEGER NOT NULL"
    ]
    
    entity_columns = [
        f"{entity_code}_valid BOOLEAN DEFAULT FALSE" for entity_code in protocol_data.keys()
    ]
    
    field_columns = []
    added_columns = set()

    for entity_code, fields in protocol_data.items():
        for field in fields:
            source_field = field.get("source_field")
            dest_field = field.get("dest_field")
            field_type = map_field_type(field.get("type_field", "text"))

            if source_field and source_field not in added_columns:
                source_column_definition = f"{source_field} TEXT"
                if field.get("mandatory", False):
                    source_column_definition += " NOT NULL"
                field_columns.append(source_column_definition)
                added_columns.add(source_field)
                
            if dest_field and dest_field not in added_columns:
                dest_column_definition = f"{dest_field} {field_type}"
                if field.get("mandatory", False):
                    dest_column_definition += " NOT NULL"
                field_columns.append(dest_column_definition)
                added_columns.add(dest_field)
    
    all_columns = base_columns + entity_columns + field_columns

    create_table_query = """
        CREATE TABLE IF NOT EXISTS {0} (
            {1},
            PRIMARY KEY (id_import, line_no)
        );
        ALTER TABLE {0} OWNER TO geonatadmin;
        """.format(
            table_name, 
            ',\n            '.join(all_columns)
        )

    create_indexes = []
    for field in field_columns:
        if "geom" in field:  
            index_name = f"idx_{table_name}_{field.split()[0]}"
            create_indexes.append(
                f"CREATE INDEX {index_name} ON {table_name} USING GIST ({field.split()[0]});"
            )
    
    return create_table_query + "\n" + "\n".join(create_indexes)

def check_import_table_exist(module_code: str) -> bool:
    """
    Vérifie si la table d'importation existe pour le module donné.
    """
    table_name = f"t_import_{module_code.lower()}"
    query = f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'gn_imports' AND table_name = '{table_name}');"
    try:
        result = DB.session.execute(query).scalar()
        return result
    except Exception as e:
        print(f"Erreur lors de la vérification de l'existence de la table : {str(e)}")
        return False

def create_import_table_protocol(module_code: str, sql: str):
    """
    Crée la table d'importation pour le protocole donné.
    """
    try:
        exist = check_import_table_exist(module_code)
        if exist:
            print(f"La table d'importation pour le module {module_code} existe déjà")
            return
        
        subprocess.run(["psql", DATABASE_URI, "-c", sql], check=True)
        print(f"Table d'importation créée pour le module {module_code}")
        
    except Exception as e:
        raise Exception(f"Erreur lors de la création de la table d'importation pour le module {module_code} : {str(e)}")
    