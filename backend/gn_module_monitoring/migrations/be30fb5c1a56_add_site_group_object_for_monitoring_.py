"""add site group object for monitoring module

Revision ID: be30fb5c1a56
Revises: 34253c8fa9b9
Create Date: 2024-07-12 14:42:28.611638

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "be30fb5c1a56"
down_revision = "34253c8fa9b9"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_permissions.cor_object_module (id_object ,id_module)
        VALUES
        ((select id_object from gn_permissions.t_objects where code_object = 'MONITORINGS_GRP_SITES'),
        (select id_module from gn_commons.t_modules where module_code = 'MONITORINGS'));
    """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.cor_object_module
        WHERE id_object = (select id_object from gn_permissions.t_objects where code_object = 'MONITORINGS_GRP_SITES')
        AND id_module = (select id_module from gn_commons.t_modules where module_code = 'MONITORINGS');
    """
    )
