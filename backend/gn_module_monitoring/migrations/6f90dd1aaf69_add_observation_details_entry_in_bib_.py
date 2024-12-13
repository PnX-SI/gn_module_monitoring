"""Add observation details entry in bib_tables_location

Revision ID: 6f90dd1aaf69
Revises: be30fb5c1a56
Create Date: 2024-10-21 15:35:31.740577

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f90dd1aaf69"
down_revision = "be30fb5c1a56"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_commons.bib_tables_location(table_desc, schema_name, table_name, pk_field, uuid_field_name)
        VALUES
        ('Table centralisant les détails des observations réalisées lors d''une visite sur un site', 
        'gn_monitoring', 't_observation_details', 'id_observation_detail', 'uuid_observation_detail')
        ON CONFLICT(schema_name, table_name) DO NOTHING;
               """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_commons.bib_tables_location
        WHERE schema_name = 'gn_monitoring' AND table_name = 't_observation_details';
        """
    )
