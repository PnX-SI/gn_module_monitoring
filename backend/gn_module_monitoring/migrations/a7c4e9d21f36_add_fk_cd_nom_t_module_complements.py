"""[modules] add foreign key cd_nom t_module_complements to taxref

Revision ID: a7c4e9d21f36
Revises: bbdd47114b4d_rename_permissions
Create Date: 2026-11-01 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c4e9d21f36"
down_revision = "bbdd47114b4d_rename_permissions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        constraint_name="t_module_complements_cd_nom_fkey",
        source_table="t_module_complements",
        referent_table="taxref",
        local_cols=["cd_nom"],
        remote_cols=["cd_nom"],
        source_schema="gn_monitoring",
        referent_schema="taxonomie",
    )


def downgrade():
    op.drop_constraint(
        constraint_name="t_module_complements_cd_nom_fkey",
        table_name="t_module_complements",
        schema="gn_monitoring",
        type_="foreignkey",
    )
