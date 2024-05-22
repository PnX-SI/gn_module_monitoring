"""add cd_nom t_module_complements

Revision ID: 398f94b364f7
Revises: 3ffeea74a9dd
Create Date: 2023-12-20 13:52:18.563621

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "398f94b364f7"
down_revision = "3ffeea74a9dd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        schema="gn_monitoring",
        table_name="t_module_complements",
        column=sa.Column(
            "cd_nom",
            sa.Integer,
        ),
    )


def downgrade():
    op.drop_column(
        schema="gn_monitoring",
        table_name="t_module_complements",
        column_name="cd_nom",
    )
