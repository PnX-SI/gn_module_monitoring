"""remove_id_module_from_sites_groups

Revision ID: f24adb481f54
Revises: 6673266fb79c
Create Date: 2022-12-13 16:00:00.512562

"""

import sqlalchemy as sa
from alembic import op

from gn_module_monitoring import MODULE_CODE

# revision identifiers, used by Alembic.
revision = "f24adb481f54"
down_revision = "6673266fb79c"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"


def upgrade():
    op.execute(
        """
    CREATE TABLE gn_monitoring.cor_sites_group_module (
        id_sites_group int4 NOT NULL,
        id_module int4 NOT NULL,
        CONSTRAINT pk_cor_sites_group_module PRIMARY KEY (id_sites_group, id_module),
        CONSTRAINT fk_cor_sites_group_module_id_sites_group FOREIGN KEY (id_sites_group) REFERENCES gn_monitoring.t_sites_groups(id_sites_group) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_cor_sites_group_module_id_module FOREIGN KEY (id_module) REFERENCES gn_commons.t_modules(id_module) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """
    )
    statement = sa.text(
        f"""
        INSERT INTO gn_monitoring.cor_sites_group_module
            (id_sites_group, id_module)
        SELECT id_sites_group, id_module
        FROM gn_monitoring.t_sites_groups; 
        """
    )
    op.execute(statement)
    op.drop_column("t_sites_groups", "id_module", schema=monitorings_schema)


def downgrade():
    op.add_column(
        "t_sites_groups",
        sa.Column(
            "id_module",
            sa.Integer(),
            sa.ForeignKey(
                f"gn_commons.t_modules.id_module",
                name="fk_t_sites_groups_id_module",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=True,
        ),
        schema=monitorings_schema,
    )

    # LIMITATION: On ne prend que le premier module associé
    statement = sa.text(
        f"""
        WITH sgm AS (
            SELECT id_sites_group , min(id_module)
            FROM gn_monitoring.cor_sites_group_module
            GROUP BY id_sites_group
        )
        UPDATE gn_monitoring.t_sites_groups AS tsg
            SET id_module = sgm.id_module
        FROM sgm
        WHERE tsg.id_sites_group = sgm.id_sites_group;
        """
    )
    op.execute(statement)

    op.alter_column("t_sites_groups", "id_module", nullable=False, schema=monitorings_schema)
    op.execute(
        """
    DROP TABLE gn_monitoring.cor_sites_group_module;
    """
    )
