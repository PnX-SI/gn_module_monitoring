"""rename_individuals_permissions

Revision ID: bbdd47114b4d
Revises: 3d39820c9ab7
Create Date: 2026-08-03 16:47:09.315441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbdd47114b4d_rename_permissions'
down_revision = '3d39820c9ab7'
branch_labels = None
depends_on = 'ad8b797d89c0'


def upgrade():
    conn = op.get_bind()

    op.execute(
        sa.text(
        """
        DELETE FROM gn_permissions.t_objects
        WHERE code_object = 'MONITORINGS_INDIVIDUALS'
        """
        )
    )


def downgrade():
    conn = op.get_bind()

    op.execute(
        sa.text(
        """
        INSERT INTO gn_permissions.t_objects (id_object, code_object, description_object)
        VALUES(nextval('gn_permissions.t_objects_id_object_seq'::regclass), 'MONITORINGS_INDIVIDUALS', 'Permissions sur les individus');    
        """
        )
    )
