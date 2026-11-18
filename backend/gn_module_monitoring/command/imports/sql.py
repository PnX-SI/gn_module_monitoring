from gn_module_monitoring.command.imports.utils import map_field_type_sqlalchemy
from gn_module_monitoring.monitoring.import_actions.entity_import_actions_utils import (
    EntityImportActionsUtils,
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    PrimaryKeyConstraint,
    text,
)

from geonature.utils.env import DB
from geonature.core.imports.models import (
    TImports,
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


def is_native_field(entity, dest_field: str) -> bool:
    """
    Un champ est natif si son store est lié à une colonne du modèle de l'entité
    (`store.native_attr`). Le store est lu sur l'entité chargée, à partir du nom de la
    colonne de destination (préfixe retiré). Un champ sans store est additionnel.
    """
    column_name = EntityImportActionsUtils.get_destination_column_name(dest_field)
    field = entity.data["fields"].get(column_name)
    return field is not None and field["store"].native_attr is not None


def get_imports_table_metadata(module_code: str, protocol_data) -> Table:
    """
    Génère la table transitoire d'importation (SQLAlchemy).

    Pour chaque champ :
    - `src_<nom>` : valeur lue dans le fichier, toujours conservée ;
    - `<nom>` : colonne de destination, présente si le champ a un `dest_field`.
      Son type vient de `type_column`, sauf pour les champs date et uuid :
        - champ natif (store lié à une colonne du modèle) : type SQL `Date` ou `UUID` ;
        - champ additionnel (stocké dans la colonne JSON de l'entité) : texte.

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

    added_columns = set()
    module = get_module(module_code)
    for entity_code, entity_fields in protocol_data.items():
        entity = module.entities[entity_code]
        all_fields = entity_fields["fields"]
        for field in all_fields:
            source_field = field.get("source_field")
            dest_field = field.get("dest_field")
            type_column = field.get("type_column", "text").lower()
            type_field = field.get("type_field")

            if source_field and source_field not in added_columns:
                columns.append(
                    Column(
                        source_field,
                        (
                            JSONB
                            if (
                                type_column in ["varchar[]", "integer[]", "jsonb"]
                                and type_field != "observers"
                            )
                            else String
                        ),
                        nullable=True,  # Must be nullable because we perform partial inserts
                    )
                )
                added_columns.add(source_field)

            if dest_field and dest_field not in added_columns:
                if type_column in ["date", "uuid"] and not is_native_field(entity, dest_field):
                    column_type = String
                else:
                    column_type = map_field_type_sqlalchemy(type_column)
                columns.append(
                    Column(
                        dest_field, column_type, nullable=True
                    )  # Must be nullable because dest_field values are computed after the row is created
                )
                added_columns.add(dest_field)

    schema = "gn_imports"

    return Table(table_name, metadata, *columns, schema=schema)
