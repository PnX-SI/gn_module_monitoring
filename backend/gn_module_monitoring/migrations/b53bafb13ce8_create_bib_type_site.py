"""create_bib_type_site

Revision ID: b53bafb13ce8
Revises: e78003460441
Create Date: 2022-12-06 16:18:24.512562

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b53bafb13ce8"
down_revision = "e78003460441"
branch_labels = None
depends_on = None

monitorings_schema = "gn_monitoring"
nomenclature_schema = "ref_nomenclatures"


def upgrade():
    op.create_table(
        "bib_type_site",
        sa.Column(
            "id_nomenclature_type_site",
            sa.Integer(),
            sa.ForeignKey(
                f"{nomenclature_schema}.t_nomenclatures.id_nomenclature",
                name="fk_t_nomenclatures_id_nomenclature_type_site",
            ),
            nullable=False,
            unique=True,
        ),
        sa.PrimaryKeyConstraint("id_nomenclature_type_site"),
        sa.Column("config", sa.JSON(), nullable=True),
        schema=monitorings_schema,
    )

    # FIXME: if sqlalchemy >= 1.4.32, it should work with postgresql_not_valid=True: cleaner
    # op.create_check_constraint(
    #     "ck_bib_type_site_id_nomenclature_type_site",
    #     "bib_type_site",
    #     f"{nomenclature_schema}.check_nomenclature_type_by_mnemonique(id_nomenclature_type_site,'TYPE_SITE')",
    #     schema=monitorings_schema,
    #     postgresql_not_valid=True
    # )
    statement = sa.text(
        f"""
        ALTER TABLE {monitorings_schema}.bib_type_site
        ADD
          CONSTRAINT ck_bib_type_site_id_nomenclature_type_site CHECK (
            {nomenclature_schema}.check_nomenclature_type_by_mnemonique(
              id_nomenclature_type_site, 'TYPE_SITE' :: character varying
            )
          ) NOT VALID
        """
    )
    op.execute(statement)
    op.create_table_comment(
        "bib_type_site",
        "Table de définition des champs associés aux types de sites",
        schema=monitorings_schema,
    )



def downgrade():
    op.drop_table("bib_type_site", schema=monitorings_schema)
