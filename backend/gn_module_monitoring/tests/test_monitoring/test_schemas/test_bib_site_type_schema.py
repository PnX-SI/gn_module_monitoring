import pytest

from sqlalchemy import select

from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import BibTypeSite
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema


@pytest.mark.usefixtures("temporary_transaction")
class TestBibSiteTypeSchema:
    def test_dump(self, types_site):
        one_type_site = db.session.scalars(select(BibTypeSite).limit(1)).first()
        schema = BibTypeSiteSchema()
        type_site = schema.dump(one_type_site)

        assert type_site["id_nomenclature_type_site"] == one_type_site.id_nomenclature_type_site
