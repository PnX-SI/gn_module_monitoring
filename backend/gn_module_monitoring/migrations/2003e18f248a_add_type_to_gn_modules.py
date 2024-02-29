"""Add type to gn_modules

Revision ID: 2003e18f248a
Revises: 362cf9d504ec
Create Date: 2022-12-19 14:01:42.559701

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2003e18f248a"
down_revision = "362cf9d504ec"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE gn_commons.t_modules AS tm SET type='monitoring_module'
        FROM gn_monitoring.t_module_complements AS tmc
        WHERE tm.id_module = tmc.id_module;
    """
    )


def downgrade():
    op.execute(
        """
        UPDATE gn_commons.t_modules AS tm SET type=NULL
        FROM gn_monitoring.t_module_complements AS tmc
        WHERE tm.id_module = tmc.id_module;
    """
    )
