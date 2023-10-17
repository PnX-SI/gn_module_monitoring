"""add geom column to sites_group

Revision ID: f3413cccdfa8
Revises: f24adb481f54
Create Date: 2023-09-26 10:57:18.886119

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision = 'f3413cccdfa8'
down_revision = 'f24adb481f54'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE gn_monitoring.t_sites_groups
        ADD COLUMN geom
            public.geometry(geometry, 4326) NULL,
        ADD COLUMN geom_local
            public.geometry(geometry, 2154) NULL,
        ADD COLUMN altitude_min
                int4 NULL,
        ADD COLUMN altitude_max
                int4 NULL;
        """
    )

    # version sqlalchemy
    # op.add_column(
    # schema="gn_monitoring",
    #     table_name="t_sites_groups",
    #     column=sa.Column(
    #         "geom",
    #         geoalchemy2.types.Geometry(geometry_type='GEOMETRY'),
    #         nullable=True,
    #     )
    # )

    # op.add_column(
    # schema="gn_monitoring",
    #     table_name="t_sites_groups",
    #     column=sa.Column(
    #         "geom_local",
    #         geoalchemy2.types.Geometry(geometry_type='GEOMETRY'),
    #         nullable=True,
    #     )
    # )

    op.execute(
        """
        ALTER TABLE gn_monitoring.t_sites_groups
	        ADD CONSTRAINT enforce_srid_geom CHECK ((st_srid(geom) = 4326));
        """

    )

    op.execute(
        """
        CREATE INDEX idx_t_sites_groups_geom ON gn_monitoring.t_sites_groups USING gist (geom);
        """
    )

    op.execute(
         """
        create trigger tri_calculate_geom_local before
        insert
            or
        update
            on
            gn_monitoring.t_sites_groups for each row execute function ref_geo.fct_trg_calculate_geom_local('geom',
            'geom_local');
        create trigger tri_t_sites_groups_calculate_alt before
        insert
            or
        update
            on
            gn_monitoring.t_sites_groups for each row execute function ref_geo.fct_trg_calculate_alt_minmax('geom');
        create trigger tri_insert_calculate_altitude before
        insert
            on
            gn_monitoring.t_sites_groups for each row execute function ref_geo.fct_trg_calculate_alt_minmax('geom');
        create trigger tri_update_calculate_altitude before
        update
            of geom_local,
            geom on
            gn_monitoring.t_sites_groups for each row execute function ref_geo.fct_trg_calculate_alt_minmax('geom');

         """       

    )


def downgrade():

    op.execute(
        """
        DROP TRIGGER tri_calculate_geom_local
            ON gn_monitoring.t_sites_groups;
        DROP TRIGGER tri_t_sites_groups_calculate_alt
            ON gn_monitoring.t_sites_groups;
        DROP TRIGGER tri_insert_calculate_altitude
            ON gn_monitoring.t_sites_groups;
        DROP TRIGGER tri_update_calculate_altitude
            ON gn_monitoring.t_sites_groups;
        """
    )

    op.execute(
        """
        ALTER TABLE gn_monitoring.t_sites_groups
        DROP COLUMN geom,
        DROP COLUMN geom_local,
        DROP COLUMN altitude_min,
        DROP COLUMN altitude_max;
        """
        )
    



