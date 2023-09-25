"""add_id_digitiser_to_t_observations

Revision ID: a5dce2633e4c
Revises: e2b66850b5ee
Create Date: 2023-09-15 16:44:29.133863

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5dce2633e4c"
down_revision = "e2b66850b5ee"
branch_labels = None
depends_on = None


monitorings_schema = "gn_monitoring"
table = "t_observations"
column = "id_digitiser"

foreign_schema = "utilisateurs"
table_foreign = "t_roles"
foreign_key = "id_role"


def upgrade():
    op.add_column(
        table,
        sa.Column(
            column,
            sa.Integer(),
            sa.ForeignKey(
                f"{foreign_schema}.{table_foreign}.{foreign_key}",
                name=f"fk_{table}_{column}",
                onupdate="CASCADE",
            ),
            nullable=False,
        ),
        schema=monitorings_schema,
    )


def downgrade():
    statement = sa.text(
        f"""
        ALTER TABLE {monitorings_schema}.{table} DROP CONSTRAINT fk_t_sites_groups_id_digitiser;
        """
    )
    op.execute(statement)
    op.drop_column(table, column, schema=monitorings_schema)
