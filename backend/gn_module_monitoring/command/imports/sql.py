from gn_module_monitoring.command.imports.utils import map_field_type_sqlalchemy
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
)

from geonature.utils.env import DB
from geonature.core.imports.models import (
    TImports,
)


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


def create_sql_import_table_protocol(module_code: str, protocol_data):
    """Create import table using SQLAlchemy metadata"""
    table = get_imports_table_metadata(module_code, protocol_data)
    table.metadata.create_all(DB.engine)
    print(f"La table transitoire d'importation pour {module_code} a été créée.")


def get_imports_table_metadata(module_code: str, protocol_data) -> Table:
    """Generate import table using SQLAlchemy metadata"""
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

    added_columns = set()
    for entity_code, entity_fields in protocol_data.items():
        all_fields = entity_fields["generic"] + entity_fields["specific"]
        for field in all_fields:
            source_field = field.get("source_field")
            dest_field = field.get("dest_field")
            type_column = field.get("type_column", "text").lower()
            field_type = map_field_type_sqlalchemy(type_column)

            if source_field and source_field not in added_columns:
                columns.append(
                    Column(
                        source_field,
                        JSONB if type_column in ["varchar[]", "integer[]", "jsonb"] else String,
                        nullable=True,  # Must be nullable because we perform partial inserts
                    )
                )
                added_columns.add(source_field)

            if dest_field and dest_field not in added_columns:
                columns.append(
                    Column(
                        dest_field, field_type, nullable=True
                    )  # Must be nullable because dest_field values are computed after the row is created
                )
                added_columns.add(dest_field)

    schema = "gn_imports"

    return Table(table_name, metadata, *columns, schema=schema)
