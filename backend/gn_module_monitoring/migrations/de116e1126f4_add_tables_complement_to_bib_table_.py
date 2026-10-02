"""add tables complement to bib_table_location

Revision ID: de116e1126f4
Revises: fc90d31c677f
Create Date: 2023-10-02 14:13:16.385139

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "de116e1126f4"
down_revision = "fc90d31c677f"
branch_labels = None
depends_on = None

common_schema = "gn_commons"
table_location = "bib_tables_location"
monitorings_schema = "gn_monitoring"
column_uiid = "uuid"


def upgrade():
    conn = op.get_bind()
    list_table_desc_to_add_uuid = [
        ("t_sites_groups", ""),
        (
            "t_site_complements",
            "Table centralisant les informations complémentaires, spécifiques aux sites faisant l''objet de protocole de suivis",
        ),
        (
            "t_visit_complements",
            "Table centralisant les informations complémentaires, spécifiques aux visites faisant l''objet de protocole de suivis",
        ),
        (
            "t_observation_complements",
            "Table centralisant les informations complémentaires, spécifiques aux observations faisant l''objet de protocole de suivis",
        ),
    ]
    for table, description in list_table_desc_to_add_uuid:
        if table != "t_sites_groups":
            pk_name_column = conn.execute(
                f"SELECT Col.Column_Name from INFORMATION_SCHEMA.TABLE_CONSTRAINTS Tab, INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE Col  WHERE Col.Constraint_Name = Tab.Constraint_Name AND Col.Table_Name = Tab.Table_Name AND Constraint_Type = 'PRIMARY KEY' AND Col.Table_Name = '{table}' "
            ).fetchone()[0]
            uuid_column = "uuid_" + table
            op.add_column(
                table,
                sa.Column(
                    uuid_column,
                    UUID(as_uuid=True),
                    nullable=False,
                    server_default=sa.text("uuid_generate_v4()"),
                ),
                schema=monitorings_schema,
            )

            statement = sa.text(
                f"""
                INSERT INTO {common_schema}.{table_location} (table_desc, schema_name, table_name, pk_field, uuid_field_name)
                VALUES
                ('{description}', '{monitorings_schema}', '{table}', '{pk_name_column}', '{uuid_column}')
                """
            )
            op.execute(statement)

        statement_add_trigger = sa.text(
            f"""
            create trigger tri_log_changes after
            insert
                or
            delete
                or
            update
                on
            {monitorings_schema}.{table} for each row execute function gn_commons.fct_trg_log_changes();
            """
        )
        op.execute(statement_add_trigger)


def downgrade():
    tables_to_drop = ("t_site_complements", "t_observation_complements", "t_visit_complements")
    statement = sa.text(
        f"""
        DELETE FROM {common_schema}.{table_location}
        WHERE table_name IN {tables_to_drop}
        """
    )
    op.execute(statement)

    tables_to_drop = tables_to_drop + ("t_sites_groups",)
    for table in tables_to_drop:
        if table != "t_sites_groups":
            uuid_column = "uuid_" + table
            op.drop_column(schema=monitorings_schema, table_name=table, column_name=uuid_column)

        statement_drop_trriger = sa.text(
            f"""
            DROP TRIGGER tri_log_changes
            ON {monitorings_schema}.{table};
            """
        )
        op.execute(statement_drop_trriger)
