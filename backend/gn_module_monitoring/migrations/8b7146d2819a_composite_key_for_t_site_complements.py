"""composite key for t_site_complements

Revision ID: 8b7146d2819a
Revises: e78003460441
Create Date: 2023-07-04 09:37:14.210507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b7146d2819a"
down_revision = "e78003460441"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE gn_monitoring.t_site_complements
            DROP CONSTRAINT pk_t_site_complements;
        ALTER TABLE gn_monitoring.t_site_complements
            ADD CONSTRAINT pk_t_site_complements PRIMARY KEY (id_base_site, id_module);
    """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE gn_monitoring.t_site_complements
            DROP CONSTRAINT pk_t_site_complements;
        ALTER TABLE gn_monitoring.t_site_complements
            ADD CONSTRAINT pk_t_site_complements PRIMARY KEY (id_base_site);
    """
    )
