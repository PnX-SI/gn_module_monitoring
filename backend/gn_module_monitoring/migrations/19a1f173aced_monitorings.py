"""monitorings

Revision ID: 19a1f173aced
Revises: 
Create Date: 2021-04-26 16:43:02.369290

"""
from alembic import op
import sqlalchemy as sa
from gn_module_monitoring import MODULE_CODE


# revision identifiers, used by Alembic.
revision = '19a1f173aced'
down_revision = None
branch_labels = ('monitorings',)
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
            '{1}',
            '{1}',
            '{2}',
            '_self',
            'fa-puzzle-piece',
            TRUE,
            TRUE
        )
    """.format(MODULE_CODE, MODULE_CODE.lower()))
    pass


def downgrade():
    pass
    op.execute(f"DELETE FROM gn_commons.t_modules WHERE module_code = '{MODULE_CODE}'")
