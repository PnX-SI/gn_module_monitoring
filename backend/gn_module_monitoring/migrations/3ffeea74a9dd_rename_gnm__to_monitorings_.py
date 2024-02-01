"""Rename GNM_ to MONITORINGS_

Revision ID: 3ffeea74a9dd
Revises: a5498a5f6022
Create Date: 2023-10-02 12:00:30.382163

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3ffeea74a9dd"
down_revision = "a5498a5f6022"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE gn_permissions.t_objects
               SET code_object = REPLACE(code_object, 'GNM_', 'MONITORINGS_')
        WHERE code_object like 'GNM_%'
               """
    )


def downgrade():
    op.execute(
        """
        UPDATE gn_permissions.t_objects
               SET code_object = REPLACE(code_object, 'MONITORINGS_', 'GNM_')
        WHERE code_object like 'MONITORINGS_%'
    """
    )
