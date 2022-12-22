"""create_cor_module_category

Revision ID: a54bafb13ce8
Revises: 
Create Date: 2022-12-06 16:18:24.512562

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a54bafb13ce8"
down_revision = "f24adb481f54"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"
referent_schema = "gn_commons"


def upgrade():
    op.create_table(
        "cor_module_categorie",
        sa.Column(
            "id_categorie",
            sa.Integer(),
            sa.ForeignKey(
                f"{monitorings_schema}.bib_categorie_site.id_categorie",
                name="fk_cor_module_categorie_id_categorie",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("id_module", sa.Integer(),sa.ForeignKey(
                f"{referent_schema}.t_modules.id_module",
                name="fk_cor_module_categorie_id_module",
                ondelete="CASCADE",
                onupdate="CASCADE",
            ), nullable=False),
        sa.PrimaryKeyConstraint("id_categorie", "id_module", name="pk_cor_module_categorie"),
        schema=monitorings_schema,
    )


def downgrade():
    op.drop_table("cor_module_categorie", schema=monitorings_schema)
