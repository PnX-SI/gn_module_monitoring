"""create_cor_site_type_category

Revision ID: e64bafb13ce8
Revises: 
Create Date: 2022-12-06 16:18:24.512562

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e64bafb13ce8"
down_revision = "a54bafb13ce8"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"
referent_schema = "ref_nomenclatures"


def upgrade():
    op.create_table(
        "cor_site_type_categorie",
        sa.Column(
            "id_categorie",
            sa.Integer(),
            sa.ForeignKey(
                f"{monitorings_schema}.bib_categorie_site.id_categorie",
                name="fk_cor_site_type_categorie_id_categorie",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("id_nomenclature", sa.Integer(),sa.ForeignKey(
                f"{referent_schema}.t_nomenclatures.id_nomenclature",
                name="fk_cor_site_type_categorie_id_type",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ), nullable=False),
        sa.PrimaryKeyConstraint("id_categorie", "id_nomenclature", name="pk_cor_site_type_categorie"),
        schema=monitorings_schema,
    )


def downgrade():
    op.drop_table("cor_site_type_categorie", schema=monitorings_schema)
