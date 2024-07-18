"""add type_grp_site

Revision ID: f61414635a9c
Revises: be30fb5c1a56
Create Date: 2024-07-18 13:53:54.871668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f61414635a9c'
down_revision = 'be30fb5c1a56'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
    """
    INSERT INTO ref_nomenclatures.bib_nomenclatures_types
    (mnemonique, label_default, definition_default, label_fr, definition_fr  )
    VALUES( 'TYPE_GRP_SITE', 'Type de groupe de site', 'Nomenclature décrivant les type de groupe de site (monitoring)',
    'Type de groupe de site', 'Nomenclature décrivant les type de groupe de site (monitoring)'
    );
    """
    )

    op.execute(
        """
        alter table gn_monitoring.t_module_complements 
        add column id_nomenclature_type_grp_site integer 
        constraint id_nomenclature_type_grp_site_fk references ref_nomenclatures.t_nomenclatures
        ON update CASCADE
        """
    )

    op.execute(
        """
        alter table gn_monitoring.t_sites_groups
        add column id_nomenclature_type_grp_site integer
        constraint id_nomenclature_type_grp_site_fk references ref_nomenclatures.t_nomenclatures
        ON update cascade;
        """
    )


def downgrade():
    op.execute(
    """
        delete from ref_nomenclatures.bib_nomenclatures_types 
        where mnemonique = 'TYPE_GRP_SITE';
    """ 
    )
    op.execute(
    """
        alter table gn_monitoring.t_module_complements 
        drop column id_nomenclature_type_grp_site;
    """
    )
    op.execute(
        """
        alter table gn_monitoring.t_sites_groups 
        drop column id_nomenclature_type_grp_site;
        """
    )
