import os
from pathlib import Path

from flask import current_app
from sqlalchemy import and_, text, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert
import sqlalchemy as sa

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    Date,
    ARRAY,
    Text,
    JSON,
    ForeignKey,
)

from geonature.utils.env import DB
from geonature.core.gn_permissions.models import (
    PermObject,
    PermissionAvailable,
    PermAction,
    cor_object_module,
)
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.imports.models import (
    BibFields,
    Destination,
    Entity,
    EntityField,
    BibThemes,
    TImports,
)
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes


from gn_module_monitoring.config.utils import (
    json_from_file,
    monitoring_module_config_path,
    validate_json_file,
    SUB_MODULE_CONFIG_DIR,
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
    "ALL": {"label": "données", "actions": ["C", "R", "U", "D"]},
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
    "observation_detail": "t_observations_details",
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
    "medias": "varchar[]",
    "date": "date",
    "nomenclature": "integer",
    "datalist": "integer",
    "text": "varchar",
    "textarea": "text",
    "integer": "integer",
    "jsonb": "jsonb",
    "time": "varchar",
    "taxonomy": "integer",
    "site": "integer",
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

    # Hack : The user needs this permission to be able to select the protocol in the destinations list.
    print(f"Création des permissions pour {module_code} : ALL")
    insert_module_available_permissions(module_code, "ALL", session=session)


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

        stmt = delete(TModules).where(TModules.id_module == module.id_module)
        DB.session.execute(stmt)

        stmt = delete(Destination).where(Destination.id_module == module.id_module)
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
        with DB.session.begin_nested():
            destination = upsert_bib_destination(module_data)
            id_destination = destination.id_destination
            module_code = module_data["module_code"]

            protocol_data, entity_hierarchy_map = get_protocol_data(module_code, id_destination)

            insert_bib_field(protocol_data)

            insert_entities(
                protocol_data, id_destination, entity_hierarchy_map, label_entity=destination.label
            )

            insert_entity_field_relations(protocol_data, id_destination, entity_hierarchy_map)

            create_sql_import_table_protocol(module_code, protocol_data)
            DB.session.commit()
    except Exception as e:
        DB.session.rollback()
        print(f"Erreur lors du traitement du module {module_data['module_code']}: {str(e)}")
        raise


def validate_json_file_protocol(module_code: str):
    errors = []
    module_config_dir = Path(monitoring_module_config_path(module_code))
    config_path = module_config_dir / "config.json"
    valid_type_widgets = set(TYPE_WIDGET.keys())
    errors.extend(validate_json_file(config_path, valid_type_widgets))

    try:
        entities = get_entities_protocol(module_code)
        for entity_code in entities:
            if not entity_code == "sites_group":
                # Valid specific file
                specific_path = module_config_dir / f"{entity_code}.json"
                errors.extend(validate_json_file(specific_path, valid_type_widgets))

                # Valid generic file
                project_root = Path(__file__).parent.parent
                generic_path = project_root / "config" / "generic" / f"{entity_code}.json"
                errors.extend(validate_json_file(generic_path, valid_type_widgets))
    except Exception as e:
        errors.append(f"Erreur lors de la lecture des entités: {str(e)}")

    return len(errors) == 0, errors


def upsert_bib_destination(module_data: dict) -> Destination:
    """
    Ajoute ou met à jour une destination dans bib_destinations.

    Args:
        module_data (dict): Données de la table gn_commons.t_modules du module à importer.

    Returns:
        Destination: L'objet Destination inséré ou mis à jour (SQLAlchemy model)
    """
    exists = DB.session.execute(
        sa.exists().where(Destination.code == module_data["module_code"]).select()
    ).scalar()

    if exists:
        existing_destination = DB.session.execute(
            select(Destination).filter_by(code=module_data["module_code"])
        ).scalar_one()

        data = {
            "label": module_data["module_label"],
            "table_name": f"t_imports_{module_data['module_code'].lower()}",
            "module_code": module_data["module_code"],
        }
        for key, value in data.items():
            setattr(existing_destination, key, value)
        DB.session.flush()
        return existing_destination

    module_monitoring_code = DB.session.execute(
        select(TModules).filter_by(module_code=module_data["module_code"])
    ).scalar_one()
    destination_data = {
        "id_module": module_monitoring_code.id_module,
        "code": module_data["module_code"],
        "label": module_data["module_label"],
        "table_name": f"t_imports_{module_data['module_code'].lower()}",
    }
    destination = Destination(**destination_data)
    DB.session.add(destination)
    DB.session.flush()
    return destination


def get_protocol_data(module_code: str, id_destination: int):
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
    entity_hierarchy_map = {}
    module_config_dir_path = monitoring_module_config_path(module_code)
    entities = get_entities_protocol(module_code)

    module_config_path = module_config_dir_path / "config.json"
    module_config = json_from_file(module_config_path)
    tree = module_config.get("tree", {}).get("module", {})

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    for entity_code in entities:
        file_path = module_config_dir_path / f"{entity_code}.json"
        specific_data = json_from_file(file_path)

        generic_data_path = os.path.join(project_root, "config", "generic", f"{entity_code}.json")
        generic_data = json_from_file(generic_data_path, result_default={})

        parent_entity = get_entity_parent(tree, entity_code)
        uuid_column = generic_data.get("id_field_name")

        entity_hierarchy_map[entity_code] = {
            "uuid_column": uuid_column,
            "parent_entity": parent_entity,
        }

        protocol_data[entity_code] = prepare_fields(
            specific_data, generic_data, entity_code, id_destination
        )

    # Add observation_detail if exists the file exists
    if "observation" in entities:
        observation_detail_specific_path = module_config_dir_path / "observation_detail.json"
        observation_detail_generic_path = os.path.join(
            project_root, "config", "generic", "observation_detail.json"
        )

        if observation_detail_specific_path.exists():
            specific_data = json_from_file(observation_detail_specific_path)
            generic_data = json_from_file(observation_detail_generic_path, result_default={})
            protocol_data["observation_detail"] = prepare_fields(
                specific_data, generic_data, "observation_detail", id_destination
            )
            entity_hierarchy_map["observation_detail"] = {
                "uuid_column": generic_data.get("id_field_name"),
                "parent_entity": "observation",
            }

    return protocol_data, entity_hierarchy_map


def prepare_fields(specific_data, generic_data, entity_code, id_destination):
    """
    Prépare les champs (fields) à insérer dans bib_fields à partir des données spécifiques et génériques.
    Organise les données sous deux clés : 'generic' et 'specific'.
    """
    entity_fields = {
        "generic": [],
        "specific": [],
        "label": specific_data.get("label", generic_data.get("label", entity_code)),
    }

    ignored_fields = ["id_module"]

    generic_fields = generic_data.get("generic", {})
    for field_name, generic_field_data in generic_fields.items():
        if field_name in ignored_fields:
            continue
        if field_name in specific_data.get("specific", {}):
            field_data = {**generic_field_data, **specific_data["specific"][field_name]}
            entity_fields["specific"].append(
                get_bib_field(field_data, entity_code, field_name, id_destination)
            )
        else:
            field_data = generic_field_data
            entity_fields["generic"].append(
                get_bib_field(field_data, entity_code, field_name, id_destination)
            )

    additional_fields = set(specific_data.get("specific", {}).keys()).difference(
        generic_fields.keys()
    )
    for field_name in additional_fields:
        if field_name in ignored_fields:
            continue
        field_data = specific_data["specific"][field_name]
        entity_fields["specific"].append(
            get_bib_field(field_data, entity_code, field_name, id_destination)
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
        "date": "varchar",
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

    if type_widget in ["checkbox", "multiselect"]:
        return "varchar[]"

    if type_widget in type_mapping:
        return type_mapping[type_widget].upper()

    if type_widget == "number":
        return "integer"

    if type_widget == "bool_checkbox":
        return "boolean"

    return "varchar"


def get_bib_field(field_data, entity_code, field_name, id_destination: int):
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

    if entity_code == "sites_group":
        name_field = f"g__{field_name}"
    elif entity_code == "observation_detail":
        name_field = f"d__{field_name}"
    else:
        name_field = f"{entity_code[0]}__{field_name}"

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
        "source_field": f"src_{field_name}",
        "dest_field": field_name,
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
            "mandatory_conditions": field.get("mandatory_conditions", []),
            "optional_conditions": field.get("optional_conditions", []),
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

    for field in all_fields:
        upsert_field(field)


def insert_entities(unique_fields, id_destination, entity_hierarchy_map, label_entity=None):
    """
    Insère ou met à jour les entités dans bib_entities en respectant la hiérarchie du tree.
    """
    inserted_entities = {}
    order = 1

    for entity_code, fields in unique_fields.items():
        entity_config = entity_hierarchy_map.get(entity_code)

        uuid_column = entity_config["uuid_column"]
        parent_entity = entity_config["parent_entity"]

        uuid_field = next(
            (
                f
                for field_type in ["generic", "specific"]
                for f in fields[field_type]
                if f["dest_field"] == uuid_column
            ),
            None,
        )

        id_field = (
            DB.session.query(BibFields.id_field)
            .filter_by(name_field=uuid_field["name_field"], id_destination=id_destination)
            .scalar()
        )

        id_parent = inserted_entities.get(parent_entity) if parent_entity else None

        entity_code_obs_detail = (
            "obs_detail" if entity_code == "observation_detail" else entity_code
        )

        entity_data = {
            "id_destination": id_destination,
            "code": entity_code_obs_detail,
            "label": fields["label"][:64] if fields["label"] else entity_code,
            "order": order,
            "validity_column": f"{entity_code.lower()}_valid",
            "destination_table_schema": "gn_monitoring",
            "destination_table_name": TABLE_NAME_SUBMODULDE.get(entity_code),
            "id_unique_column": id_field,
            "id_parent": id_parent,
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
                inserted_entity_id = DB.session.execute(
                    select(Entity.id_entity).filter_by(
                        code=entity_code_obs_detail, id_destination=id_destination
                    )
                ).scalar()

        inserted_entities[entity_code] = inserted_entity_id
        DB.session.flush()


def get_themes_dict():
    """Récupère les thèmes depuis bib_themes"""
    themes = DB.session.execute(
        select(BibThemes.id_theme, BibThemes.name_theme).filter(
            BibThemes.name_theme.in_(["general_info", "additional_data"])
        )
    ).all()
    return {theme.name_theme: theme.id_theme for theme in themes}


def get_entity_ids_dict(protocol_data, id_destination):
    """Récupère les IDs des entités depuis bib_entities"""
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
    """Insère les relations entre les entités et les champs dans cor_entity_field"""
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
            parent_uuid = entity_hierarchy_map[parent_code]["uuid_column"]
            get_cor_entity_field(
                entity_id=entity_id,
                field_name=f"{parent_code[0]}__{parent_uuid}",
                id_destination=id_destination,
                bib_themes=bib_themes,
                is_parent_link=True,
            )


def get_cor_entity_field(
    entity_id, field_name, id_destination, bib_themes, order=None, is_parent_link=False
):
    """Crée une relation entre une entité et un champ dans cor_entity_field"""
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


def map_field_type_sqlalchemy(type_widget: str):
    """Map widget types to SQLAlchemy column types"""
    type_mapping = {
        "varchar": String,
        "varchar[]": ARRAY(String),
        "text": Text,
        "boolean": Boolean,
        "integer": Integer,
        "integer[]": ARRAY(Integer),
        "date": Date,
        "jsonb": JSON,
    }
    return type_mapping.get(type_widget.lower(), String)


def get_imports_table_metadata(module_code: str, protocol_data) -> Table:
    """Generate import table using SQLAlchemy metadata"""
    metadata = MetaData()

    columns = [
        Column(
            "id_import",
            Integer,
            ForeignKey(TImports.id_import, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("line_no", Integer, nullable=False),
    ]

    columns.extend(
        [
            Column(f"{entity_code}_valid", Boolean, default=False)
            for entity_code in protocol_data.keys()
        ]
    )

    added_columns = set()
    for entity_code, entity_fields in protocol_data.items():
        all_fields = entity_fields["generic"] + entity_fields["specific"]
        for field in all_fields:
            source_field = field.get("source_field")
            dest_field = field.get("dest_field")
            field_type = map_field_type_sqlalchemy(field.get("type_column", "text"))

            if source_field and source_field not in added_columns:
                columns.append(
                    Column(source_field, String, nullable=not field.get("mandatory", False))
                )
                added_columns.add(source_field)

            if dest_field and dest_field not in added_columns:
                columns.append(
                    Column(dest_field, field_type, nullable=not field.get("mandatory", False))
                )
                added_columns.add(dest_field)

    table_name = f"t_imports_{module_code.lower()}"
    schema = "gn_imports"

    return Table(table_name, metadata, *columns, schema=schema)


def create_sql_import_table_protocol(module_code: str, protocol_data):
    """Create import table using SQLAlchemy metadata"""
    table = get_imports_table_metadata(module_code, protocol_data)
    table.metadata.create_all(DB.engine)
    print(f"La table transitoire d'importation pour {module_code} a été créée.")


def check_rows_exist_in_import_table(module_code: str) -> bool:
    """Vérifie si la table d'importation contient des données."""
    table_name = f"t_imports_{module_code.lower()}"
    query = f"SELECT * FROM gn_imports.{table_name} LIMIT 1;"
    try:
        result = DB.session.execute(query).fetchone()
        return result is not None
    except Exception as e:
        print(f"Erreur lors de la vérification de l'existence de la table : {str(e)}")
        return False


def ask_confirmation():
    prompt = (
        "\nVeuillez confirmer que vous souhaitez effectuer avec ces modifications ? [yes/no]: "
    )

    response = input(prompt).strip().lower()

    while response not in ["yes", "y", "no", "n"]:
        print("Réponse invalide. Veuillez répondre par 'yes' ou 'no'.")
        response = input(prompt).strip().lower()

    return response in ["yes", "y"]


def compare_protocol_fields(existing_fields, new_fields):
    """
    Compare les champs existants avec les nouveaux champs pour identifier les différences.

    Args:
        existing_fields: Liste des champs existants en base
        new_fields: Liste des nouveaux champs depuis les fichiers JSON

    Returns:
        - Liste des champs à ajouter
        - Liste des champs à mettre à jour
        - Liste des champs à supprimer
    """
    existing_by_name = {f["name_field"]: f for f in existing_fields}
    new_by_name = {f["name_field"]: f for f in new_fields}

    to_add = []
    to_update = []
    to_delete = []

    for name, new_field in new_by_name.items():
        if name not in existing_by_name:
            to_add.append(new_field)
        else:
            existing = existing_by_name[name]
            if has_field_changes(existing, new_field):
                to_update.append(new_field)

    for name in existing_by_name:
        if name not in new_by_name:
            to_delete.append(existing_by_name[name])

    return to_add, to_update, to_delete


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


def get_existing_protocol_state(id_destination: int, module_data):
    """
    Récupère l'état actuel du protocole en base de données.
    """
    fields_query = select(BibFields).filter_by(id_destination=id_destination)
    existing_fields = DB.session.execute(fields_query).scalars().all()

    entities_query = select(Entity).filter_by(id_destination=id_destination)
    existing_entities = DB.session.execute(entities_query).scalars().all()

    entity = DB.session.execute(select(Entity).filter_by(id_destination=id_destination)).scalar()
    new_label = module_data["module"].get("module_label")

    return {
        "fields": [field.__dict__ for field in existing_fields],
        "entities": [entity.__dict__ for entity in existing_entities],
        "label": True if entity and entity.label != new_label else False,
    }


def process_update_module_import(module_data, module_code: str):
    """
    Gère la mise à jour complète d'un module.
    """
    try:
        is_valid, messages, fields_to_delete, update_label_only = validate_protocol_changes(
            module_code, module_data
        )

        if is_valid is None:
            return None

        if not is_valid:
            print("Erreurs détectées lors de la validation du protocole:")
            for msg in messages:
                print(f"- {msg}")
            return False

        if messages:
            print("\nAvertissements concernant les modifications du protocole:")
            for msg in messages:
                print(f"- {msg}")

        if not ask_confirmation():
            return False
        else:
            return update_protocol(module_data, module_code, fields_to_delete, update_label_only)

    except Exception as e:
        print(f"Erreur lors du traitement du module {module_code}: {str(e)}")
        return False


def validate_protocol_changes(module_code: str, module_data):
    """
    Valide les changements dans les fichiers de configuration du protocole.

    Args:
        module_code: Code du module à valider.

    Returns:
        - Booléen indiquant si la validation a réussi.
        - Liste des messages d'erreur ou d'avertissement.
        - Champs à supprimer.
        - Booléen indiquant si seule la mise à jour du label est nécessaire.
    """
    try:
        destination = DB.session.execute(select(Destination).filter_by(code=module_code)).scalar()

        if check_rows_exist_in_import_table(module_code):
            return (
                False,
                [
                    "La table d'importation contient des données. Impossible de mettre à jour le protocole."
                ],
                [],
                False,
            )

        existing_data = get_existing_protocol_state(destination.id_destination, module_data)
        protocol_data, _ = get_protocol_data(module_code, destination.id_destination)

        all_new_fields = []
        for entity_fields in protocol_data.values():
            for field_type in ["generic", "specific"]:
                all_new_fields.extend(entity_fields[field_type])

        fields_to_add, fields_to_update, fields_to_delete = compare_protocol_fields(
            existing_data["fields"], all_new_fields
        )

        warnings = []
        if existing_data["label"]:
            warnings.append(
                f"INFO: Le libellé du module va être modifié. {destination.label} -> {module_data['module'].get('module_label')}"
            )

        if fields_to_delete:
            warnings.append(
                "ATTENTION: Des champs vont être supprimés. "
                f"Champs concernés: {', '.join(f['name_field'][3:] for f in fields_to_delete)}"
            )

        if fields_to_update:
            warnings.append(
                "ATTENTION: Des champs vont être modifiés. "
                f"Champs concernés: {', '.join(f['name_field'][3:] for f in fields_to_update)}"
            )

        if fields_to_add:
            warnings.append(
                "INFO: De nouveaux champs vont être ajoutés. "
                f"Champs concernés: {', '.join(f['name_field'][3:] for f in fields_to_add)}"
            )

        if (
            not fields_to_add
            and not fields_to_update
            and not fields_to_delete
            and existing_data["label"]
        ):
            return True, warnings, [], True

        if (
            not fields_to_add
            and not fields_to_update
            and not fields_to_delete
            and not existing_data["label"]
        ):
            warnings.append("Aucun changement détecté dans le protocole.")
            return None, warnings, [], False

        return True, warnings, fields_to_delete, False

    except Exception as e:
        return False, [f"Erreur lors de la validation du protocole: {str(e)}"], [], False


def update_protocol(module_data, module_code, fields_to_delete, update_label_only=False):
    """
    Met à jour un protocole existant ou uniquement le libellé de l'entité dans `bib_entities`.

    Args:
        module_data: Données du module à mettre à jour.
        module_code: Code du module.
        fields_to_delete: Liste des champs à supprimer.
        update_label_only: Si vrai, met à jour uniquement le label de l'entité.

    Returns:
        Booléen indiquant si la mise à jour a réussi.
    """
    try:
        DB.session.rollback()
        module_label = module_data["module"].get("module_label")

        destination = DB.session.execute(
            select(Destination).filter_by(code=module_code)
        ).scalar_one()

        if update_label_only:
            update_entity_label(destination.id_destination, module_label)
            DB.session.commit()
            return True

        protocol_data, entity_hierarchy_map = get_protocol_data(
            module_code, destination.id_destination
        )

        with DB.session.begin_nested():

            insert_bib_field(protocol_data)

            insert_entities(
                protocol_data,
                destination.id_destination,
                entity_hierarchy_map,
                label_entity=module_label,
            )

            insert_entity_field_relations(
                protocol_data, destination.id_destination, entity_hierarchy_map
            )

            if fields_to_delete:
                delete_bib_fields(fields_to_delete)

            table_name = f"t_imports_{module_code.lower()}"
            DB.engine.execute(f"DROP TABLE IF EXISTS gn_imports.{table_name}")

            create_sql_import_table_protocol(module_code, protocol_data)

        DB.session.commit()
        return True

    except Exception as e:
        DB.session.rollback()
        print(f"Erreur lors de la mise à jour du protocole : {str(e)}")
        return False


def delete_bib_fields(fields):
    """
    Supprime les champs de la table bib_fields.
    """
    field_ids = [f["id_field"] for f in fields]
    DB.session.execute(delete(BibFields).where(BibFields.id_field.in_(field_ids)))
    DB.session.flush()


def update_entity_label(destination_id: int, new_label: str):
    """
    Met à jour tous les libellés des entités associées à une même destination dans la table `Entity`.

    Args:
        destination_id: ID de la destination associée.
        new_label: Nouveau libellé à appliquer à toutes les entités.
    """
    entities = (
        DB.session.execute(select(Entity).filter_by(id_destination=destination_id)).scalars().all()
    )
    for entity in entities:
        if entity.label != new_label:
            entity.label = new_label
            DB.session.add(entity)

    print(f"Libellé de l'entité mis à jour : {entity.label} -> {new_label}")
    DB.session.flush()
