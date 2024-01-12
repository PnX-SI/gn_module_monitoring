import pytest

from sqlalchemy import select

from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import BibTypeSite


@pytest.mark.usefixtures("temporary_transaction")
class TestBibTypeSite:
    def test_get_bib_type_site(self, types_site):
        type_site = list(types_site.values())[0]
        get_type_site = db.session.execute(
            select(BibTypeSite).where(
                BibTypeSite.id_nomenclature_type_site == type_site.id_nomenclature_type_site
            )
        ).scalar_one()

        assert get_type_site.id_nomenclature_type_site == type_site.id_nomenclature_type_site

    def test_get_all_bib_type_site(self, types_site):
        get_types_site = db.session.scalars(select(BibTypeSite)).all()

        assert all(
            type_site.id_nomenclature_type_site
            in [get_type_site.id_nomenclature_type_site for get_type_site in get_types_site]
            for type_site in types_site.values()
        )
