"""insert_sample_marking_type

Revision ID: 89a5299ce02e
Revises: 398f94b364f7
Create Date: 2024-06-28 11:35:32.173070

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "89a5299ce02e"
down_revision = "398f94b364f7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    INSERT INTO ref_nomenclatures.t_nomenclatures (id_type,cd_nomenclature,mnemonique,label_default,definition_default,label_fr) VALUES
     (ref_nomenclatures.get_id_nomenclature_type('TYP_MARQUAGE'),'1','Peinture','Peinture','Peinture','Peinture');
    """
    )


def downgrade():
    op.execute(
        """
    DELETE FROM ref_nomenclatures.t_nomenclatures
    WHERE id_type = ref_nomenclatures.get_id_nomenclature_type('TYP_MARQUAGE')
    """
    )
