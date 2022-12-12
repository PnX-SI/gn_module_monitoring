"""remove_id_module_from_sites_complements

Revision ID: 6673266fb79c
Revises: a54bafb13ce8
Create Date: 2022-12-13 16:00:00.512562

"""
import sqlalchemy as sa
from alembic import op

from gn_module_monitoring import MODULE_CODE

# revision identifiers, used by Alembic.
revision = "6673266fb79c"
down_revision = "a54bafb13ce8"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"


def upgrade():
    # Transfert data to core_site_module table
    statement = sa.text(
        f"""
        INSERT INTO {monitorings_schema}.cor_site_module (id_module, id_base_site)
        SELECT tsc.id_module, tsc.id_base_site
        FROM {monitorings_schema}.t_site_complements AS tsc
        LEFT JOIN  {monitorings_schema}.cor_site_module AS csm
        ON tsc.id_base_site = csm.id_base_site
        WHERE csm.id_base_site IS NULL;
        """
    )
    op.execute(statement)

    # Drop column id_module
    op.drop_column("t_site_complements", "id_module", schema=monitorings_schema)


def downgrade():
    op.add_column(
        "t_site_complements",
        sa.Column(
            "id_module",
            sa.Integer(),
            sa.ForeignKey(
                f"gn_commons.t_modules.id_module",
                name="fk_t_site_complements_id_module",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=True,
        ),
        schema=monitorings_schema,
    )
    # Cannot use orm here because need the model to be "downgraded" as well
    # Need to set nullable True above for existing rows
    # LIMITATION: Assume that current use is one site associated to one module
    statement = sa.text(
        f"""
        WITH sm AS (
            SELECT min(id_module) AS first_id_module, id_base_site
            FROM {monitorings_schema}.cor_site_module AS csm
            GROUP BY id_base_site
        )
        UPDATE {monitorings_schema}.t_site_complements sc
            SET id_module = sm.first_id_module
        FROM sm
        WHERE sm.id_base_site = sc.id_base_site;
        """
    )
    op.execute(statement)
    op.alter_column("t_site_complements", "id_module", nullable=False, schema=monitorings_schema)
