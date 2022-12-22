import pytest
from flask import url_for

from gn_module_monitoring.tests.fixtures.site import categories, site_type, sites


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestSite:
    def test_get_categories_by_id(self, categories):
        for cat in categories.values():
            r = self.client.get(
                url_for(
                    "monitorings.get_categories_by_id",
                    id_categorie=cat.id_categorie,
                )
            )
            assert r.json["label"] == cat.label

    def test_get_categories(self, categories):
        r = self.client.get(url_for("monitorings.get_categories"))

        assert r.json["count"] >= len(categories)
        assert all([cat.as_dict(depth=1) in r.json["categories"] for cat in categories.values()])

    def test_get_categories_label(self, categories):
        label = list(categories.keys())[0]

        r = self.client.get(url_for("monitorings.get_categories"), query_string={"label": label})
        assert categories[label].as_dict(depth=1) in r.json["categories"]

    def test_get_sites(self, sites):
        r = self.client.get(url_for("monitorings.get_sites"))

        assert r.json["count"] >= len(sites)
        assert any([site.as_dict() in r.json["sites"] for site in sites.values()])

    def test_get_module_sites(self):
        module_code = "TEST"
        r = self.client.get(url_for("monitorings.get_module_sites", module_code=module_code))

        assert r.json["module_code"] == module_code
