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

TYPE_SITE = "TYPE_SITE"


def upgrade():
    op.create_table(
        "bib_type_site",
        sa.Column(
            "id_nomenclature",
            sa.Integer(),
            sa.ForeignKey(
                f"{nomenclature_schema}.t_nomenclatures.id_nomenclature",
                name="fk_t_nomenclatures_id_nomenclature",
            ),
            nullable=False,
            unique=True,
        ),
        sa.PrimaryKeyConstraint("id_nomenclature"),
        sa.Column("config", sa.JSON(), nullable=True),
        schema=monitorings_schema,
    )

    statement = sa.text(
        f"""
        CREATE OR REPLACE FUNCTION {monitorings_schema}.ck_bib_type_site_id_nomenclature()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
                perform {nomenclature_schema}.check_nomenclature_type_by_mnemonique(NEW.id_nomenclature, :mnemonique );
                RETURN NEW;
        END;
        $function$
        ;
        DROP TRIGGER IF EXISTS ck_bib_type_site_id_nomenclature on gn_monitoring.bib_type_site;
        CREATE TRIGGER ck_bib_type_site_id_nomenclature BEFORE
        INSERT
            OR
        UPDATE ON {monitorings_schema}.bib_type_site FOR EACH ROW EXECUTE PROCEDURE {monitorings_schema}.ck_bib_type_site_id_nomenclature();
        """
    ).bindparams(mnemonique=TYPE_SITE)
    op.execute(statement)


def downgrade():

    op.drop_table("bib_type_site", schema=monitorings_schema)
    statement = sa.text(
        f"""
        DROP FUNCTION IF EXISTS {monitorings_schema}.ck_bib_type_site_id_nomenclature;
        """
    )
    op.execute(statement)
