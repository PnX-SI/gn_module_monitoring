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
        assert all([schema.dump(cat) in r.json["items"] for cat in categories.values()])

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

    def test_get_sites_limit(self, sites):
        limit = 34

        r = self.client.get(url_for("monitorings.get_sites", limit=limit))

        assert len(r.json["items"]) == limit

    def test_get_sites_base_site_name(self, sites):
        site = list(sites.values())[0]
        base_site_name = site.base_site_name

        r = self.client.get(url_for("monitorings.get_sites", base_site_name=base_site_name))

        assert len(r.json["items"]) == 1
        assert r.json["items"][0]["base_site_name"] == base_site_name

    def test_get_sites_id_base_site(self, sites):
        site = list(sites.values())[0]
        id_base_site = site.id_base_site

        r = self.client.get(url_for("monitorings.get_sites", id_base_site=id_base_site))

        assert len(r.json["items"]) == 1
        assert r.json["items"][0]["id_base_site"] == id_base_site

    def test_get_module_sites(self):
        module_code = "TEST"
        r = self.client.get(url_for("monitorings.get_module_sites", module_code=module_code))

        assert r.json["module_code"] == module_code
