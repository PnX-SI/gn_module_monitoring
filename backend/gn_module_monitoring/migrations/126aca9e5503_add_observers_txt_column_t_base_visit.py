"""add_observers_txt_column_t_base_visit

Revision ID: 126aca9e5503
Revises: e2b66850b5ee
Create Date: 2023-09-12 11:49:24.535949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "126aca9e5503"
down_revision = "a5dce2633e4c"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"
table = "t_base_visits"
column = "observers_txt"


def upgrade():
    op.add_column(
        table,
        sa.Column(
            column,
            sa.Text(),
            nullable=True,
        ),
        schema=monitorings_schema,
    )


def downgrade():
    op.drop_column(table, column, schema=monitorings_schema)
