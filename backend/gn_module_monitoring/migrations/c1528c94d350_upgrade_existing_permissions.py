"""Upgrade existing permissions

Revision ID: c1528c94d350
Revises: 3ffeea74a9dd
Create Date: 2023-10-02 12:09:53.695122

"""
from alembic import op
import sqlalchemy as sa

from click.testing import CliRunner

from gn_module_monitoring.command.cmd import process_available_permissions
from gn_module_monitoring.command.utils import installed_modules

# revision identifiers, used by Alembic.
revision = "c1528c94d350"
down_revision = "3ffeea74a9dd"
branch_labels = None
depends_on = None


def upgrade():
    # Création des permissions disponibles pour chaque module
    for module in installed_modules():
        process_available_permissions(module["module_code"])

    # ########
    # Mise à jour des permissions existantes vers les sous objets
    # Création des permission des sous-objets à partir des permissions contenus dans l'objet ALL
    op.execute(
        """
        WITH ap AS (
            SELECT o.code_object,o.id_object, tpa.id_module
            FROM gn_permissions.t_permissions_available AS tpa
            JOIN gn_permissions.t_objects AS o
            ON o.id_object = tpa.id_object AND NOT code_object = 'ALL'
            JOIN gn_commons.t_modules AS tm
            ON tm.id_module = tpa.id_module AND tm."type" = 'monitoring_module'
            JOIN gn_permissions.bib_actions AS ba
            ON tpa.id_action = ba.id_action
            WHERE NOT (code_object = 'MONITORINGS_MODULES' AND ba.code_action = 'U')
        ), ep AS (
                SELECT id_role, id_action, tp.id_module , tp.id_object, scope_value, sensitivity_filter
                FROM gn_permissions.t_permissions AS tp
                JOIN gn_permissions.t_objects AS o
                ON o.id_object = tp.id_object AND code_object = 'ALL'
                JOIN gn_commons.t_modules AS tm
                ON tm.id_module = tp.id_module AND tm."type" = 'monitoring_module'
        ), new_p AS (
            SELECT DISTINCT ep.id_role, ep.id_action, ep.id_module, ap.id_object, ep.scope_value, ep.sensitivity_filter
            FROM ep
            JOIN ap
            ON ep.id_module = ap.id_module
            LEFT OUTER JOIN  gn_permissions.t_permissions AS p
            ON p.id_role = ep.id_role
            AND  p.id_action = ep.id_action
            AND  p.id_module = ep.id_module
            AND  p.id_object = ap.id_object
            WHERE p.id_permission IS NULL
        )
        INSERT INTO gn_permissions.t_permissions
        (id_role, id_action, id_module, id_object, scope_value, sensitivity_filter)
        SELECT id_role, id_action, id_module, id_object, scope_value, sensitivity_filter
        FROM new_p;
    """
    )

    #  Suppression des permissions available inutile
    #  on conserve POUR all
    #  R : accès au module
    #  U : modification des paramètres du module
    #  E : Exporter les données du module
    op.execute(
        """
        WITH to_del AS (
            SELECT tp.*
            FROM gn_permissions.t_permissions_available AS tp
            JOIN gn_commons.t_modules AS tm
            ON tm.id_module = tp.id_module AND tm."type" = 'monitoring_module'
            JOIN gn_permissions.t_objects AS o
            ON o.id_object = tp.id_object AND code_object = 'ALL'
            JOIN gn_permissions.bib_actions AS ba
            ON tp.id_action = ba.id_action AND NOT ba.code_action  IN ('R', 'E', 'U')
        )
        DELETE FROM gn_permissions.t_permissions_available AS tp
        USING to_del td
        WHERE  tp.id_module = td.id_module
        AND tp.id_object = td.id_object
        AND tp.id_action = td.id_action
        AND tp."label" = td."label"
        AND tp.scope_filter = td.scope_filter
        AND tp.sensitivity_filter = td.sensitivity_filter;
    """
    )

    # Suppression des permissions qui ne sont pas dans les permissions available
    op.execute(
        """
        WITH to_del AS (
            SELECT tp.id_permission
            FROM gn_permissions.t_permissions AS tp
            JOIN gn_commons.t_modules AS tm
            ON tm.id_module = tp.id_module AND tm."type" = 'monitoring_module'
            LEFT OUTER JOIN gn_permissions.t_permissions_available AS ta
            ON tp.id_action = ta.id_action
            AND tp.id_module = ta.id_module
            AND tp.id_object = ta.id_object
            WHERE ta.id_module  IS NULL
        )
        DELETE FROM  gn_permissions.t_permissions AS tp
        WHERE tp.id_permission IN (SELECT id_permission FROM to_del);
    """
    )


def downgrade():
    pass
