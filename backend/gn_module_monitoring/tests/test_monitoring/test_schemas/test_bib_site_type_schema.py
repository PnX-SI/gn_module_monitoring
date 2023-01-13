import pytest

from gn_module_monitoring.monitoring.models import BibTypeSite
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema


@pytest.mark.usefixtures("temporary_transaction")
class TestBibSiteTypeSchema:
    def test_dump(self, types_site):
        one_type_site = BibTypeSite.query.first()
        schema = BibTypeSiteSchema()
        type_site = schema.dump(one_type_site)

        assert type_site["id_nomenclature"] == one_type_site.id_nomenclature
