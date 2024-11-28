"""add id_import column for each entity

Revision ID: df277299fdda
Revises: 6f90dd1aaf69
Create Date: 2024-11-28 18:20:49.512808

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "df277299fdda"
down_revision = "6f90dd1aaf69"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        schema="gn_monitoring",
        table_name="t_base_sites",
        column=sa.Column("id_import", sa.Integer, nullable=True),
    )
    op.add_column(
        schema="gn_monitoring",
        table_name="t_base_visits",
        column=sa.Column("id_import", sa.Integer, nullable=True),
    )
    op.add_column(
        schema="gn_monitoring",
        table_name="t_observations",
        column=sa.Column("id_import", sa.Integer, nullable=True),
    )


def downgrade():
    op.drop_column(
        schema="gn_monitoring",
        table_name="t_base_sites",
        column_name="id_import",
    )
    op.drop_column(
        schema="gn_monitoring",
        table_name="t_base_visits",
        column_name="id_import",
    )
    op.drop_column(
        schema="gn_monitoring",
        table_name="t_observations",
        column_name="id_import",
    )
