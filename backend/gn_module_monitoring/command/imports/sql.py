import re

from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy import (
    ARRAY,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    Uuid,
    inspect as sa_inspect,
    text,
)

from geonature.utils.env import DB
from geonature.core.imports.models import (
    TImports,
)

from gn_module_monitoring.tools.stores import UsersStore
from gn_module_monitoring.monitoring.import_actions.entity_import_actions_utils import (
    EntityImportActionsUtils,
)


def check_rows_exist_in_import_table(module_code: str) -> bool:
    """
    Vérifie si la table d'importation contient des données.

    Parameters
    ----------
    module_code : str
        Code du module

    Returns
    -------
    bool
        True si la table contient des données, False si la table est vide ou si une erreur se produit.
    """
    table_name = f"t_imports_{module_code.lower()}"
    query = f"SELECT * FROM gn_imports.{table_name} LIMIT 1;"
    try:
        with DB.session.begin_nested():
            result = DB.session.execute(text(query)).fetchone()
        return result is not None
    except Exception as e:
        print(f"Erreur lors de la vérification de l'existence de la table : {str(e)}")
        return False


def create_sql_import_table_protocol(module_code: str, protocol_data):
    """
    Crée la table transitoire du protocole.

    La table est recréée à chaque appel : une table existante (installation précédente
    du module, dont le schéma peut être différent) est supprimée avant.
    """
    table = get_imports_table_metadata(module_code, protocol_data)
    DB.session.execute(text(f"DROP TABLE IF EXISTS {table.fullname}"))
    table.metadata.create_all(DB.session.connection())
    print(f"La table transitoire d'importation pour {module_code} a été créée.")


def get_field_store(entity, field_name: str):
    """
    Store du champ de l'entité chargée (`entity.data["fields"]`), à partir du nom de la colonne
    (`field_name` : nom de la colonne de la table transitoire, préfixe retiré). None si le champ
    n'est pas dans la configuration de l'entité.
    """
    column_name = EntityImportActionsUtils.get_destination_column_name(field_name)
    field = entity.data["fields"].get(column_name)
    return None if field is None else field["store"]


def is_native_field(store) -> bool:
    """
    Un champ est natif si son store est lié à une colonne du modèle de l'entité
    (`store.native_attr`). Un champ sans store est additionnel.
    """
    return store is not None and store.native_attr is not None


def get_destination_column_type(store):
    """
    Type SQLAlchemy de la colonne de destination (dest_field) dans la table transitoire.

    Il vient du store (`store.get_column_type()`). Les types date, datetime et uuid ne sont
    conservés que pour un champ natif : un champ additionnel (stocké dans la colonne JSON de
    l'entité) est lu en texte.
    """
    if store.sql_type in (Date, DateTime, Uuid) and not is_native_field(store):
        return String
    return store.get_column_type()


def get_imports_table_metadata(module_code: str, protocol_data) -> Table:
    """
    Génère la table transitoire d'importation (SQLAlchemy).

    Pour chaque champ :
    - `src_<nom>` : valeur lue dans le fichier, toujours conservée (texte, JSONB pour les listes) ;
    - `<nom>` : colonne de destination, présente si le champ a un `dest_field`. Son type vient du
      store du champ (`store.get_column_type()`), voir `get_destination_column_type`.
      Les observateurs (store users) sont lus en texte à la source, mappés ensuite.

    Pour chaque entité, `<entité>_data` (JSONB, nullable) reçoit les valeurs mises en forme
    des champs additionnels.

    Parameters
    ----------
    module_code : str
        Code du module
    protocol_data : dict
        Dictionnaire contenant la config du protocole

    Returns
    -------
    Table
        objet `Table` de la table transitoire d'importation
    """
    metadata = MetaData()
    table_name = f"t_imports_{module_code.lower()}"
    columns = [
        Column(
            "id_import",
            Integer,
            ForeignKey(TImports.id_import, onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("line_no", Integer, nullable=False),
        PrimaryKeyConstraint("id_import", "line_no", name=f"pk_{table_name}"),
    ]

    for entity_code in protocol_data.keys():
        columns.append(Column(f"{entity_code}_valid", Boolean, default=False))
        if entity_code != "observation":
            columns.append(Column(f"{entity_code}_line_no", Integer))
        columns.append(Column(f"{entity_code}_data", JSONB, nullable=True))

    # Import local : évite le cycle command.imports -> modules -> config -> command.imports
    from gn_module_monitoring.modules import get_module
    from gn_module_monitoring.tools.stores import UsersStore

    added_columns = set()
    module = get_module(module_code)
    for entity_code, entity_fields in protocol_data.items():
        entity = module.entities[entity_code]
        all_fields = entity_fields["fields"]
        for field in all_fields:
            source_field = field.get("source_field")
            dest_field = field.get("dest_field")
            store = get_field_store(entity, field["name_field"])
            sql_type = None if store is None else store.sql_type
            # Les observateurs (store users) sont lus en texte : ce sont des noms, mappés ensuite
            is_observers = isinstance(store, UsersStore)

            if source_field and source_field not in added_columns:
                columns.append(
                    Column(
                        source_field,
                        (
                            JSONB
                            if isinstance(sql_type, ARRAY) and not is_observers
                            else String
                        ),
                        nullable=True,  # Must be nullable because we perform partial inserts
                    )
                )
                added_columns.add(source_field)

            if dest_field and dest_field not in added_columns:
                column_type = get_destination_column_type(store) if store is not None else String
                columns.append(
                    Column(
                        dest_field, column_type, nullable=True
                    )  # Must be nullable because dest_field values are computed after the row is created
                )
                added_columns.add(dest_field)

    schema = "gn_imports"

    return Table(table_name, metadata, *columns, schema=schema)


# Alias PostgreSQL : même type pour le moteur (`format_type`), écrits différemment selon l'origine
# (DDL SQLAlchemy compilé en PostgreSQL, ou reflet de `information_schema`).
PG_TYPE_ALIASES = {
    "FLOAT": "DOUBLE PRECISION",
    "FLOAT8": "DOUBLE PRECISION",
    "INT": "INTEGER",
    "INT4": "INTEGER",
    "INT8": "BIGINT",
    "INT2": "SMALLINT",
    "BOOL": "BOOLEAN",
    "CHARACTER VARYING": "VARCHAR",
    "CHARACTER": "CHAR",
    "TIMESTAMP": "TIMESTAMP WITHOUT TIME ZONE",
    "TIMESTAMPTZ": "TIMESTAMP WITH TIME ZONE",
    "TIME": "TIME WITHOUT TIME ZONE",
}


def normalize_pg_type(type_str: str) -> str:
    """
    Forme normalisée d'un type PostgreSQL compilé, pour comparer deux types équivalents.

    Exemples : `FLOAT` et `DOUBLE PRECISION` donnent `DOUBLE PRECISION` ;
    `DATETIME` / `TIMESTAMP` donnent `TIMESTAMP WITHOUT TIME ZONE` ; `CHAR(32)` reste distinct de `UUID`.
    """
    text_ = " ".join(str(type_str).strip().upper().split())
    match = re.fullmatch(r"([A-Z][A-Z0-9_ ]*?)\s*(\(.*\))?\s*((?:\[\])*)", text_)
    if not match:
        return text_
    base, args, dims = match.group(1), match.group(2) or "", match.group(3)
    base = PG_TYPE_ALIASES.get(base, base)
    return f"{base}{args}{dims}"


def compare_transient_columns(db_types: dict, expected_types: dict) -> dict:
    """
    Compare les colonnes réellement présentes en base aux colonnes attendues.

    Parameters
    ----------
    db_types : dict
        `{nom de colonne: type PostgreSQL compilé}` lu en base.
    expected_types : dict
        `{nom de colonne: type PostgreSQL compilé}` généré depuis le protocole.

    Returns
    -------
    dict
        `added` (attendues, absentes en base), `removed` (présentes en base, non attendues),
        `type_changed` (`{"name", "db", "expected"}`, types différents après normalisation).
    """
    added = [name for name in expected_types if name not in db_types]
    removed = [name for name in db_types if name not in expected_types]
    type_changed = [
        {"name": name, "db": db_types[name], "expected": expected_types[name]}
        for name in expected_types
        if name in db_types
        and normalize_pg_type(db_types[name]) != normalize_pg_type(expected_types[name])
    ]
    return {"added": added, "removed": removed, "type_changed": type_changed}


def get_transient_table_diff(module_code: str, protocol_data) -> dict:
    """
    Compare la table transitoire réelle (`gn_imports.t_imports_<module>`) à celle générée.

    Les types sont compilés avec le dialecte PostgreSQL, côté génération comme côté base
    (reflet via `inspect`), puis normalisés (voir `normalize_pg_type`).

    Returns
    -------
    dict
        `table` (nom complet), `exists` (table présente en base), `added`, `removed`, `type_changed`.
        Si la table n'existe pas, toutes les colonnes attendues sont `added`.
    """
    table = get_imports_table_metadata(module_code, protocol_data)
    pg_dialect = postgresql.dialect()
    expected_types = {col.name: col.type.compile(dialect=pg_dialect) for col in table.columns}

    inspector = sa_inspect(DB.session.connection())
    if not inspector.has_table(table.name, schema=table.schema):
        return {
            "table": table.fullname,
            "exists": False,
            "added": list(expected_types),
            "removed": [],
            "type_changed": [],
        }

    db_types = {
        col["name"]: col["type"].compile(dialect=pg_dialect)
        for col in inspector.get_columns(table.name, schema=table.schema)
    }
    return {
        "table": table.fullname,
        "exists": True,
        **compare_transient_columns(db_types, expected_types),
    }


def transient_table_has_diff(transient_diff: dict) -> bool:
    """Vrai si la table transitoire doit être recréée (absente ou différente)."""
    return (
        not transient_diff["exists"]
        or bool(transient_diff["added"])
        or bool(transient_diff["removed"])
        or bool(transient_diff["type_changed"])
    )
