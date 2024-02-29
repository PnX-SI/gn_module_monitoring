"""trigger moniroting

Revision ID: 7fbcdd93626a
Revises: 6a15625a0f4a
Create Date: 2024-01-11 17:25:05.135068

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7fbcdd93626a"
down_revision = "6a15625a0f4a"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DROP FUNCTION IF EXISTS gn_synthese.fct_trg_delete_synthese_observations();

        CREATE FUNCTION gn_synthese.fct_trg_delete_synthese_observations() RETURNS trigger AS $$
        BEGIN
            --Suppression des données dans la synthèse
            DELETE FROM gn_synthese.synthese WHERE unique_id_sinp = OLD.uuid_observation;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_delete_synthese_observations AFTER DELETE ON gn_monitoring.t_observations
            FOR EACH ROW EXECUTE PROCEDURE gn_synthese.fct_trg_delete_synthese_observations();


    """
    )


def downgrade():
    op.execute(
        """
        DROP TRIGGER trg_delete_synthese_observations ON gn_monitoring.t_observations;
        DROP FUNCTION IF EXISTS gn_synthese.fct_trg_delete_synthese_observations();
    """
    )
