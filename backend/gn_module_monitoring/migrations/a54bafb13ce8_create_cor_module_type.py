"""create_cor_module_type

Revision ID: a54bafb13ce8
Revises: ce54ba49ce5c
Create Date: 2022-12-06 16:18:24.512562

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a54bafb13ce8"
down_revision = "ce54ba49ce5c"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"
referent_schema = "gn_commons"


def upgrade():
    op.create_table(
        "cor_module_type",
        sa.Column(
            "id_type_site",
            sa.Integer(),
            sa.ForeignKey(
                f"{monitorings_schema}.bib_type_site.id_nomenclature_type_site",
                name="fk_cor_module_type_id_nomenclature_type_site",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "id_module",
            sa.Integer(),
            sa.ForeignKey(
                f"{referent_schema}.t_modules.id_module",
                name="fk_cor_module_type_id_module",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id_type_site", "id_module", name="pk_cor_module_type"),
        schema=monitorings_schema,
    )


def downgrade():
    op.drop_table("cor_module_type", schema=monitorings_schema)
