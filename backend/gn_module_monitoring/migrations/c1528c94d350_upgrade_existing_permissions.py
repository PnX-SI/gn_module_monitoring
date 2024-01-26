"""Upgrade existing permissions

Revision ID: c1528c94d350
Revises: 3ffeea74a9dd
Create Date: 2023-10-02 12:09:53.695122

"""

from alembic import op
import sqlalchemy as sa

from click.testing import CliRunner

from gn_module_monitoring.command.cmd import process_available_permissions
from gn_module_monitoring.command.utils import installed_modules

# revision identifiers, used by Alembic.
revision = "c1528c94d350"
down_revision = "3ffeea74a9dd"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
