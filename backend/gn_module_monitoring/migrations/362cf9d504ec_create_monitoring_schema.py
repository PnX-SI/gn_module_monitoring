"""create_monitoring_schema

Revision ID: 362cf9d504ec
Revises: 
Create Date: 2021-03-29 18:38:24.512562

"""
import importlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text, and_

from geonature.core.gn_permissions.models import TObjects
from geonature.core.gn_commons.models.base import BibTablesLocation

# revision identifiers, used by Alembic.
revision = "362cf9d504ec"
down_revision = None
branch_labels = ("monitorings",)
depends_on = ("f06cc80cc8ba",)  # GeoNature 2.7.5


monitorings_schema = "gn_monitoring"


def upgrade():
    op.execute(
        text(
            importlib.resources.read_text("gn_module_monitoring.migrations.data", "monitoring.sql")
        )
    )


def downgrade():
    op.drop_table("t_module_complements", monitorings_schema)
    op.drop_table("t_observation_complements", monitorings_schema)
    op.drop_table("t_observation_details", monitorings_schema)
    op.drop_table("t_observations", monitorings_schema)
    op.drop_table("t_site_complements", monitorings_schema)
    op.drop_table("t_sites_groups", monitorings_schema)
    op.drop_table("t_visit_complements", monitorings_schema)

    # Remove all GNM related objects
    statement = sa.delete(TObjects).where(TObjects.code_object.like("GNM_%"))
    op.execute(statement)

    # Remove monitorings related rows in bib_table_locations
    statement = sa.delete(BibTablesLocation).where(
        and_(
            BibTablesLocation.schema_name == monitorings_schema,
            BibTablesLocation.table_name.in_(
                ("t_module_complements", "t_observations", "t_sites_groups")
            ),
        )
    )
    op.execute(statement)
