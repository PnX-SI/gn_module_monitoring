"""site groups : use local srid for geom_local

Revision ID: 3d39820c9ab7
Revises: 461b82ee737a
Create Date: 2026-07-03 10:56:19.902719

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

from geonature.utils.env import DB

# revision identifiers, used by Alembic.
revision = "3d39820c9ab7"
down_revision = "461b82ee737a"
branch_labels = None
depends_on = None


def upgrade():
    local_srid = DB.session.execute(sa.func.Find_SRID("ref_geo", "l_areas", "geom")).scalar()

    site_group_srid = DB.session.execute(sa.text("""
            SELECT srid
            FROM geometry_columns
            WHERE f_table_schema = 'gn_monitoring'
            AND f_table_name = 't_sites_groups'
            AND f_geometry_column = 'geom_local'
        """)).scalar_one_or_none()

    if local_srid != site_group_srid and site_group_srid is not None:
        sql = f"""
        DROP TRIGGER IF EXISTS tri_update_calculate_altitude ON gn_monitoring.t_sites_groups;
        ALTER TABLE gn_monitoring.t_sites_groups ALTER COLUMN geom_local TYPE geometry (geometry, :local_srid) USING st_transform(geom_local, :local_srid);
        CREATE OR REPLACE TRIGGER tri_update_calculate_altitude
            BEFORE UPDATE OF geom, geom_local
            ON gn_monitoring.t_sites_groups
            FOR EACH ROW
            EXECUTE FUNCTION ref_geo.fct_trg_calculate_alt_minmax('geom');"""
        op.get_bind().execute(text(sql), local_srid=local_srid)


def downgrade():
    pass
