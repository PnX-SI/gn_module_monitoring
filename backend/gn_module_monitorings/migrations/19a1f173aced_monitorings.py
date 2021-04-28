"""monitorings

Revision ID: 19a1f173aced
Revises: 
Create Date: 2021-04-26 16:43:02.369290

"""
from alembic import op
import sqlalchemy as sa
import pkg_resources
from gn_module_monitorings import MODULE_CODE


# revision identifiers, used by Alembic.
revision = '19a1f173aced'
down_revision = None
branch_labels = ('gn_module_monitorings',)
depends_on = None # geonature


def upgrade():
    op.execute("""
INSERT INTO gn_commons.t_modules (
    module_code,
    module_label,
    module_path,
    module_target,
    module_picto,
    active_frontend,
    active_backend
) VALUES (
    '{0}',
    '{1}',
    '{1}',
    '_self',
    'fa-puzzle-piece',
    TRUE,
    TRUE
)
    """.format(MODULE_CODE, MODULE_CODE.lower()))
    monitorings = pkg_resources.resource_string("gn_module_monitorings.migrations", f"data/monitoring.sql").decode('utf-8')
    delete_synthese = pkg_resources.resource_string("gn_module_monitorings.migrations", f"data/delete_synthese.sql").decode('utf-8')
    op.execute(monitorings)
    op.execute(delete_synthese)    
    pass


def downgrade():
    op.execute(f"DELETE FROM gn_commons.t_modules WHERE module_code = '{MODULE_CODE}'")

    # delete_synthese
    op.execute(f"""
        DROP FUNCTION IF EXISTS gn_synthese.fct_trg_delete_synthese_visits() CASCADE;
        DROP FUNCTION IF EXISTS gn_synthese.fct_trg_delete_synthese_observations() CASCADE;
    """)

    # monitorings
    op.execute(f"""
        DROP TABLE IF EXISTS gn_monitoring.t_observation_details;
        DROP TABLE IF EXISTS gn_monitoring.t_observation_complements;
        DROP TABLE IF EXISTS gn_monitoring.t_observations;
        DROP TABLE IF EXISTS gn_monitoring.t_visit_complements;
        DROP TABLE IF EXISTS gn_monitoring.t_site_complements;
        DROP TABLE IF EXISTS gn_monitoring.t_sites_groups;
        DROP TABLE IF EXISTS gn_monitoring.t_module_complements;
        
        DELETE FROM gn_commons.bib_tables_location WHERE schema_name = 'gn_monitoring';
        DELETE FROM gn_permissions.t_objects 
            WHERE code_object IN ('GNM_SITES', 'GNM_VISITES', 'GNM_OBSERVATIONS', 'GNM_GRP_SITES');
    """)

    pass
