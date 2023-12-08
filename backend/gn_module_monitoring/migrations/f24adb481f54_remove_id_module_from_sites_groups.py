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
    # Cannot use orm here because need the model to be "downgraded" as well
    # Need to set nullable True above for existing rows
    # Get data from core_site_module
    # LIMITATION: Assume that current use is one site associated to one module associated to one site_group
    statement = sa.text(
        f"""
        WITH sgm AS (
            SELECT id_sites_group , csm.id_module
            FROM gn_monitoring.t_site_complements AS tsc
            JOIN gn_monitoring.cor_site_module AS csm
            ON tsc.id_base_site = csm.id_base_site
            WHERE NOT id_sites_group IS NULL
        )
        UPDATE gn_monitoring.t_sites_groups AS tsg
            SET id_module = sgm.id_module
        FROM sgm
        WHERE tsg.id_sites_group = sgm.id_sites_group;
        """
    )
    op.execute(statement)

    statement = sa.text(
        f"""
        UPDATE {monitorings_schema}.t_sites_groups
        SET id_module = (select id_module
                          from gn_commons.t_modules tm
                          where module_code = :module_code)
        WHERE id_module IS NULL;
        """
    ).bindparams(module_code=MODULE_CODE)
    op.execute(statement)
    op.alter_column("t_sites_groups", "id_module", nullable=False, schema=monitorings_schema)
