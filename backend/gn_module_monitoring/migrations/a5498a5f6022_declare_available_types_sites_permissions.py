""" declare available types sites permissions

Revision ID: a5498a5f6022
Revises: fc90d31c677f
Create Date: 2024-02-01 10:42:28.268643

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5498a5f6022"
down_revision = "fc90d31c677f"
branch_labels = None
depends_on = None


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
            AND 
            pa.id_object IN (
                SELECT to2.id_object  
                FROM gn_permissions.t_objects to2 
                WHERE code_object IN ('TYPES_SITES', 'GNM_SITES', 'GNM_GRP_SITES')
            )
        """
    )

    op.execute(
        """
        DELETE FROM
            gn_permissions.t_permissions p
        USING gn_permissions.t_objects o
            WHERE
                p.id_object = o.id_object
                AND o.code_object IN ('TYPES_SITES', 'GNM_SITES', 'GNM_GRP_SITES', 'GNM_MODULES')
            ;
        """
    )

    op.execute(
        """
        DELETE FROM
            gn_permissions.t_objects
            WHERE code_object IN ('TYPES_SITES', 'GNM_SITES', 'GNM_GRP_SITES', 'GNM_MODULES')
        ;
        """
    )
