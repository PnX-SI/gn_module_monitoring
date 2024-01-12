import pytest
from flask import url_for

from gn_module_monitoring.monitoring.models import TMonitoringVisits
from pypnusershub.tests.utils import set_logged_user_cookie
from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestVisits:
    def test_get_visits(self, visits, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_visits",
            )
        )

        expected_visits = {visit.id_base_visit for visit in visits}
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}
        assert expected_visits.issubset(current_visits)
        assert all(visit["module"] is not None for visit in r.json["items"])

    def test_get_visits_with_site(self, visits, sites, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        site = list(sites.values())[0]

        r = self.client.get(url_for("monitorings.get_visits", id_base_site=site.id_base_site))

        expected_visits = {
            visit.id_base_visit for visit in visits if visit.id_base_site == site.id_base_site
        }
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}

        assert expected_visits.issubset(current_visits)
