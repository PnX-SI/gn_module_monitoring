import pytest
from flask import url_for


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestVisits:
    def test_get_visits(self, visits):
        r = self.client.get(
            url_for(
                "monitorings.get_visits",
            )
        )

        expected_visits = {visit.id_base_visit for visit in visits}
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}
        assert expected_visits.issubset(current_visits)
        assert all(visit["module"] is not None for visit in r.json["items"])

    def test_get_visits_with_site(self, visits, sites):
        site = list(sites.values())[0]

        r = self.client.get(url_for("monitorings.get_visits", id_base_site=site.id_base_site))

        expected_visits = {
            visit.id_base_visit for visit in visits if visit.id_base_site == site.id_base_site
        }
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}

        assert expected_visits.issubset(current_visits)
