"""create_bib_categorie_site

Revision ID: b53bafb13ce8
Revises: 
Create Date: 2022-12-06 16:18:24.512562

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b53bafb13ce8"
down_revision = "362cf9d504ec"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"


def upgrade():
    op.create_table(
        "bib_categorie_site",
        sa.Column("id_categorie", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id_categorie"),
        schema=monitorings_schema,
    )
    op.create_index(
        op.f("ix_bib_categorie_site_id"),
        "bib_categorie_site",
        ["id_categorie"],
        unique=False,
        schema=monitorings_schema,
    )
    op.add_column(
        "t_base_sites",
        sa.Column(
            "id_categorie",
            sa.Integer(),
            sa.ForeignKey(
                f"{monitorings_schema}.bib_categorie_site.id_categorie",
                name="fk_t_base_sites_id_categorie",
                ondelete="CASCADE",
            ),
            nullable=True,  # TODO: see migration? nullable is conservative here
        ),
        schema=monitorings_schema,
    )


def downgrade():
    op.drop_constraint("fk_t_base_sites_id_categorie", "t_base_sites", schema=monitorings_schema)
    op.drop_column("t_base_sites", "id_categorie", schema=monitorings_schema)
    op.drop_index(
        op.f("ix_bib_categorie_site_id"),
        table_name="bib_categorie_site",
        schema=monitorings_schema,
    )
    op.drop_table("bib_categorie_site", schema=monitorings_schema)
