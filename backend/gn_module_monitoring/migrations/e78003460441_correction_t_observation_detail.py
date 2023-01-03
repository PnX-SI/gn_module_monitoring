"""Correction t_observation_detail

Revision ID: e78003460441
Revises: 2003e18f248a
Create Date: 2023-01-02 16:44:18.715547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e78003460441'
down_revision = '2003e18f248a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE gn_monitoring.t_observation_details
            DROP CONSTRAINT pk_t_observation_details;
        ALTER TABLE gn_monitoring.t_observation_details
            ADD CONSTRAINT pk_t_observation_details PRIMARY KEY (id_observation_detail);

        ALTER TABLE gn_monitoring.t_observation_details
            ADD uuid_observation_detail UUID DEFAULT uuid_generate_v4() NOT NULL;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE gn_monitoring.t_observation_details
            DROP CONSTRAINT pk_t_observation_details;
        ALTER TABLE gn_monitoring.t_observation_details
            ADD CONSTRAINT pk_t_observation_details PRIMARY KEY (id_observation);

        ALTER TABLE gn_monitoring.t_observation_details
            DROP COLUMN uuid_observation_detail;
    """)
