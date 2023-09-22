"""declare available permissions

Revision ID: fc90d31c677f
Revises: e78003460441
Create Date: 2023-06-09 10:32:21.008918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fc90d31c677f"
down_revision = "f24adb481f54"
branch_labels = None
depends_on = ("f051b88a57fd",)


def upgrade():
    op.execute(
        """
        INSERT INTO
            gn_permissions.t_objects(
            code_object,
            description_object
            )
        VALUES
            ('TYPES_SITES','Types de sites à associer aux protocoles du module MONITORINGS')
        """
    )
    op.execute(
        """
        INSERT INTO
            gn_permissions.t_permissions_available (
                id_module,
                id_object,
                id_action,
                label,
                scope_filter
            )
        SELECT
            m.id_module,
            o.id_object,
            a.id_action,
            v.label,
            v.scope_filter
        FROM
            (
                VALUES
                    ('MONITORINGS', 'ALL', 'R', False, 'Accéder au module'),
                    ('MONITORINGS', 'TYPES_SITES', 'R', False, 'Accéder aux types de site'),
                    ('MONITORINGS', 'TYPES_SITES', 'C', False, 'Créer des types de site'),
                    ('MONITORINGS', 'TYPES_SITES', 'U', False, 'Modifier des types de site'),
                    ('MONITORINGS', 'TYPES_SITES', 'D', False, 'Supprimer des types de site'),
                    ('MONITORINGS', 'GNM_SITES', 'R', True, 'Accéder aux sites'),
                    ('MONITORINGS', 'GNM_SITES', 'C', True, 'Créer des sites'),
                    ('MONITORINGS', 'GNM_SITES', 'U', True, 'Modifier des sites'),
                    ('MONITORINGS', 'GNM_SITES', 'D', True, 'Supprimer des sites'),
                    ('MONITORINGS', 'GNM_GRP_SITES', 'R', True, 'Accéder aux groupes de sites'),
                    ('MONITORINGS', 'GNM_GRP_SITES', 'C', True, 'Créer des groupes de sites'),
                    ('MONITORINGS', 'GNM_GRP_SITES', 'U', True, 'Modifier des groupes de sites'),
                    ('MONITORINGS', 'GNM_GRP_SITES', 'D', True, 'Supprimer des groupes de sites')
            ) AS v (module_code, object_code, action_code, scope_filter, label)
        JOIN
            gn_commons.t_modules m ON m.module_code = v.module_code
        JOIN
            gn_permissions.t_objects o ON o.code_object = v.object_code
        JOIN
            gn_permissions.bib_actions a ON a.code_action = v.action_code
        """
    )
    op.execute(
        """
        WITH bad_permissions AS (
            SELECT
                p.id_permission
            FROM
                gn_permissions.t_permissions p
            JOIN gn_commons.t_modules m
                    USING (id_module)
            WHERE
                m.module_code = 'MONITORINGS'
            EXCEPT
            SELECT
                p.id_permission
            FROM
                gn_permissions.t_permissions p
            JOIN gn_permissions.t_permissions_available pa ON
                (p.id_module = pa.id_module
                    AND p.id_object = pa.id_object
                    AND p.id_action = pa.id_action)
        )
        DELETE
        FROM
            gn_permissions.t_permissions p
                USING bad_permissions bp
        WHERE
            bp.id_permission = p.id_permission;
        """
    )

    op.execute(
        """
        INSERT INTO gn_permissions.t_objects (code_object, description_object)
            VALUES
                ('GNM_MODULES', 'Permissions sur les modules')
            ON CONFLICT DO NOTHING
        ;
    """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM
            gn_permissions.t_permissions_available pa
        USING
            gn_commons.t_modules m
        WHERE
            pa.id_module = m.id_module
            AND
            module_code = 'MONITORINGS'
        """
    )
