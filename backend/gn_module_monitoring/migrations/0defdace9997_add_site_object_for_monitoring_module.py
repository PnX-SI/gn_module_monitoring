"""add site object for monitoring module

Revision ID: 0defdace9997
Revises: 7fbcdd93626a
Create Date: 2024-06-17 15:45:58.888781

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0defdace9997"
down_revision = "7fbcdd93626a"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_permissions.cor_object_module (id_object ,id_module)
        VALUES
        ((select id_object from gn_permissions.t_objects where code_object = 'MONITORINGS_SITES'),
        (select id_module from gn_commons.t_modules where module_code = 'MONITORINGS'));
    """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.cor_object_module
        WHERE id_object = (select id_object from gn_permissions.t_objects where code_object = 'MONITORINGS_SITES')
        AND id_module = (select id_module from gn_commons.t_modules where module_code = 'MONITORINGS');
    """
    )
