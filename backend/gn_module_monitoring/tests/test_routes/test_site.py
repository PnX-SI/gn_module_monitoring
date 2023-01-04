import pytest
from flask import url_for

from gn_module_monitoring.monitoring.schemas import BibCategorieSiteSchema, MonitoringSitesSchema


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
        schema = BibCategorieSiteSchema()

        r = self.client.get(url_for("monitorings.get_categories"))

        assert r.json["count"] >= len(categories)
        assert all(
            [schema.dump(cat) in r.json["items"] for cat in categories.values()]
        )

    def test_get_categories_label(self, categories):
        label = list(categories.keys())[0]
        schema = BibCategorieSiteSchema()
        r = self.client.get(url_for("monitorings.get_categories"), query_string={"label": label})
        assert schema.dump(categories[label]) in r.json["items"]

    def test_get_sites(self, sites):
        schema = MonitoringSitesSchema()

        r = self.client.get(url_for("monitorings.get_sites"))

        assert r.json["count"] >= len(sites)
        assert any([schema.dump(site) in r.json["items"] for site in sites.values()])

    def test_get_module_sites(self):
        module_code = "TEST"
        r = self.client.get(url_for("monitorings.get_module_sites", module_code=module_code))

        assert r.json["module_code"] == module_code
