"""Delete object ALL

Revision ID: 6a15625a0f4a
Revises: c1528c94d350
Create Date: 2023-10-02 13:53:05.682108

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6a15625a0f4a"
down_revision = "c1528c94d350"
branch_labels = None
depends_on = None


def upgrade():
    # Suppression des permissions available de ALL pour les modules monitorings
    pass


def downgrade():
    # Creations des permissions available de ALL pour les modules monitorings
    #  a partir de GNM_MODULES
    op.execute(
        """
        INSERT INTO gn_permissions.t_permissions_available
        (id_module, id_object, id_action, "label", scope_filter, sensitivity_filter)
        SELECT
            tp.id_module,
            gn_permissions.get_id_object('ALL') AS id_object,
            tp.id_action,
            tp."label",
            tp.scope_filter,
            tp.sensitivity_filter
        FROM gn_permissions.t_permissions_available AS tp
        JOIN gn_commons.t_modules AS tm
        ON tm.id_module = tp.id_module AND tm."type" = 'monitoring_module'
        JOIN gn_permissions.t_objects AS o
        ON o.id_object = tp.id_object AND code_object = 'MONITORINGS_MODULES';
        """
    )
    # Creations des permissions de ALL pour les modules monitorings
    #  a partir de GNM_MODULES
    op.execute(
        """
        INSERT INTO gn_permissions.t_permissions
        (id_role, id_action, id_module, id_object, scope_value, sensitivity_filter)
        SELECT
            tp.id_role,
            tp.id_action,
            tp.id_module,
            gn_permissions.get_id_object('ALL') AS id_object,
            tp.scope_value,
            tp.sensitivity_filter
        FROM gn_permissions.t_permissions AS tp
        JOIN gn_commons.t_modules AS tm
        ON tm.id_module = tp.id_module AND tm."type" = 'monitoring_module'
        JOIN gn_permissions.t_objects AS o
        ON o.id_object = tp.id_object AND code_object = 'MONITORINGS_MODULES';
        """
    )
