"""[import] populate cor import dataset

Revision ID: 7f3e1a254d16
Revises: 461b82ee737a
Create Date: 2026-15-05 09:14:48.084725

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7f3e1a254d16"
down_revision = "461b82ee737a"
branch_labels = None
depends_on = ("ed1de98c65aa",)


def upgrade():
    op.execute("""
        INSERT INTO gn_imports.cor_import_datasets (id_import, id_dataset)
        SELECT DISTINCT visit.id_import, visit.id_dataset
        FROM gn_monitoring.t_base_visits visit
        WHERE visit.id_import IS NOT NULL
          AND visit.id_dataset IS NOT NULL
        ON CONFLICT (id_import, id_dataset) DO NOTHING
    """)


def downgrade():
    pass  # We can't rollback this migration. However rolling back ed1de98c65aa will rollback this migration as well.
