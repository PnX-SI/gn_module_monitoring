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
    # FIXME: find a better way because need to assign a module...
    statement = sa.text(
        f"""
         update {monitorings_schema}.t_site_complements
         set id_module = (select id_module 
                          from gn_commons.t_modules tm 
                          where module_code = :module_code);
        """
    ).bindparams(module_code=MODULE_CODE)
    op.execute(statement)
    op.alter_column("t_site_complements", "id_module", nullable=False, schema=monitorings_schema)
