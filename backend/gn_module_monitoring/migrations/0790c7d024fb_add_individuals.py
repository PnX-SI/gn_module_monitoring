"""add individuals

Revision ID: 0790c7d024fb
Revises: fc90d31c677f
Create Date: 2023-09-27 14:01:26.035798

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "0790c7d024fb"
down_revision = "fc90d31c677f"
branch_labels = None
depends_on = "84f40d008640"  # individuals (geonature)

SCHEMA = "gn_monitoring"


def upgrade():
    op.create_table(
        "t_individual_complements",
        sa.Column(
            "id_base_individual",
            sa.Integer,
            sa.ForeignKey(f"{SCHEMA}.t_base_individuals.id_base_individual", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "id_module",
            sa.Integer,
            sa.ForeignKey("gn_commons.t_modules.id_module", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("data", JSONB),
        schema=SCHEMA,
    )

    op.create_table(
        "cor_individual_module",
        sa.Column(
            "id_base_individual",
            sa.Integer,
            sa.ForeignKey(f"{SCHEMA}.t_base_individuals.id_base_individual", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "id_module",
            sa.Integer,
            sa.ForeignKey("gn_commons.t_modules.id_module", ondelete="CASCADE"),
            primary_key=True,
        ),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_table("cor_individual_module", schema=SCHEMA)
    op.drop_table("t_individual_complements", schema=SCHEMA)
