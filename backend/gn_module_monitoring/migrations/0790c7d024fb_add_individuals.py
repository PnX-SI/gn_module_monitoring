"""add individuals

Revision ID: 0790c7d024fb
Revises: fc90d31c677f
Create Date: 2023-09-27 14:01:26.035798

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = "0790c7d024fb"
down_revision = "fc90d31c677f"
branch_labels = None
depends_on = None

SCHEMA = "gn_monitoring"


def upgrade():
    op.create_table(
        "t_base_individuals",
        sa.Column("id_base_individual", sa.Integer, primary_key=True),
        sa.Column(
            "uuid_individual", UUID, nullable=False, server_default=sa.text("uuid_generate_v4()")
        ),
        sa.Column("base_individual_name", sa.Unicode(255), nullable=False),
        sa.Column("cd_nom", sa.Integer, sa.ForeignKey("taxonomie.taxref.cd_nom"), nullable=False),
        sa.Column(
            "id_nomenclature_sex",
            sa.Integer,
            sa.ForeignKey("ref_nomenclatures.t_nomenclatures.id_nomenclature"),
            server_default=sa.text(
                "ref_nomenclatures.get_default_nomenclature_value('SEXE'::character varying)"
            ),
        ),
        sa.Column("active", sa.Boolean, server_default=sa.sql.true()),
        sa.Column("comment", sa.Text),
        sa.Column(
            "id_digitiser",
            sa.Integer,
            sa.ForeignKey("utilisateurs.t_roles.id_role"),
            nullable=False,
        ),
        sa.Column("meta_create_date", sa.DateTime(timezone=False)),
        sa.Column("meta_update_date", sa.DateTime(timezone=False)),
        schema=SCHEMA,
    )

    op.create_table(
        "t_marking_events",
        sa.Column("id_marking", sa.Integer, primary_key=True),
        sa.Column(
            "id_base_individual",
            sa.Integer,
            sa.ForeignKey(f"{SCHEMA}.t_base_individuals.id_base_individual", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("marking_date", sa.DateTime(timezone=False), nullable=False),
        sa.Column(
            "id_operator",
            sa.Integer,
            sa.ForeignKey("utilisateurs.t_roles.id_role"),
            nullable=False,
        ),
        sa.Column(
            "id_base_marking_site",
            sa.Integer,
            sa.ForeignKey("gn_monitoring.t_base_sites.id_base_site"),
        ),
        sa.Column(
            "id_nomenclature_marking_type",
            sa.Integer,
            sa.ForeignKey("ref_nomenclatures.t_nomenclatures.id_nomenclature"),
            nullable=False,
        ),
        sa.Column("marking_location", sa.Unicode(255)),
        sa.Column("marking_code", sa.Unicode(255)),
        sa.Column("marking_details", sa.Text),
        sa.Column("additional_data", JSONB),
        sa.Column(
            "id_digitiser",
            sa.Integer,
            sa.ForeignKey("utilisateurs.t_roles.id_role"),
            nullable=False,
        ),
        sa.Column("meta_create_date", sa.DateTime(timezone=False)),
        sa.Column("meta_update_date", sa.DateTime(timezone=False)),
        schema=SCHEMA,
    )
    # TODO: add constraint to id_nomenclature_marking_type to check

    op.create_table(
        "t_individual_complements",
        sa.Column(
            "id_base_individual",
            sa.Integer,
            sa.ForeignKey(f"{SCHEMA}.t_base_individuals.id_base_individual", ondelete="CASCADE"),
            primary_key=True
        ),
        sa.Column(
            "id_module",
            sa.Integer,
            sa.ForeignKey("gn_commons.t_modules.id_module", ondelete="CASCADE"),
            primary_key=True
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
            primary_key=True
        ),
        sa.Column(
            "id_module",
            sa.Integer,
            sa.ForeignKey("gn_commons.t_modules.id_module", ondelete="CASCADE"),
            primary_key=True
        ),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_table("cor_individual_module", schema=SCHEMA)
    op.drop_table("t_individual_complements", schema=SCHEMA)
    op.drop_table("t_marking_events", schema=SCHEMA)
    op.drop_table("t_base_individuals", schema=SCHEMA)
