"""add individual permissions

Revision ID: 461b82ee737a
Revises: 2894b3c03c66
Create Date: 2023-11-21 14:14:48.084725

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "461b82ee737a"
down_revision = "2894b3c03c66"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_permissions.t_objects (code_object, description_object)
        VALUES ('MONITORINGS_INDIVIDUALS', 'Permissions sur les individus'),
        ('MONITORINGS_MARKINGS', 'Permissions sur les marquages');
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.t_permissions WHERE id_object in 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object in ('MONITORINGS_INDIVIDUALS', 'MONITORINGS_MARKINGS'))
        """
    )
    op.execute(
        """
        DELETE FROM gn_permissions.t_permissions_available WHERE id_object in 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object in ('MONITORINGS_INDIVIDUALS', 'MONITORINGS_MARKINGS'))
        """
    )
    op.execute(
        """
        DELETE FROM gn_permissions.t_objects where code_object in ('MONITORINGS_INDIVIDUALS', 'MONITORINGS_MARKINGS');
        """
    )
