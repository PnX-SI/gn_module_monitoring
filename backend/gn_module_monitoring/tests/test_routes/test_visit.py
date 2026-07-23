from gn_module_monitoring.tests.fixtures.module import monitoring_module
import pytest

from flask import url_for

from pypnusershub.tests.utils import set_logged_user_cookie
from geonature.utils.env import db, BACKEND_DIR
from gn_module_monitoring.monitoring.models import TMonitoringModules
from sqlalchemy import select


@pytest.mark.usefixtures("client_class", "visits")
class TestVisits:

    def test_get_visits(self, visits, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_visits",
            )
        )

        expected_visits = {visit.id_base_visit for visit in visits}
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}
        assert expected_visits.issubset(current_visits)
        assert all(visit["module"] is not None for visit in r.json["items"])

    def test_get_visits_with_site(self, visits, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]

        r = self.client.get(
            url_for(
                "monitorings.get_visits",
                id_base_site=site.id_base_site,
            )
        )

        expected_visits = {
            visit.id_base_visit for visit in visits if visit.id_base_site == site.id_base_site
        }
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}

        assert expected_visits.issubset(current_visits)

    def test_get_visit_by_id(self, visits, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = visits[0]

        r = self.client.get(
            url_for(
                "monitorings.get_visit_by_id",
                module_code="test",
                id=visit.id_base_visit,
            )
        )

        assert r.status_code == 200
        assert r.json["id_base_visit"] == visit.id_base_visit
        # `module` is explicitly excluded from the schema in get_visit_by_id
        assert "module" not in r.json

    def test_get_visit_by_id_not_found(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for(
                "monitorings.get_visit_by_id",
                module_code="test",
                id=999999999,
            )
        )

        assert r.status_code == 404

    def test_post_visit(self, visits, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]

        data = {
            "id_base_site": site.id_base_site,
            "visit_date_min": "2024-01-01",
            "id_dataset": visits[0].id_dataset,
        }

        r = self.client.post(
            url_for(
                "monitorings.post_visit",
                module_code="test",
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_base_site"] == site.id_base_site
        assert r.json["visit_date_min"] == data["visit_date_min"]

    def test_patch_visit(self, visits, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = visits[0]

        data = {
            "id_base_site": visit.id_base_site,
            "visit_date_min": "2024-02-02",
        }

        r = self.client.patch(
            url_for(
                "monitorings.patch_visit",
                module_code="test",
                _id=visit.id_base_visit,
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_base_visit"] == visit.id_base_visit
        assert r.json["visit_date_min"] == data["visit_date_min"]

    def test_patch_visit_not_found(self, visits, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        module_code = "test"

        r = self.client.patch(
            url_for(
                "monitorings.patch_visit",
                module_code=module_code,
                _id=999999999,
                object_type="visit",
            ),
            json={},
        )

        assert r.status_code == 404

    def test_delete_visit(self, visits, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = visits[-1]

        r = self.client.delete(
            url_for(
                "monitorings.delete_visit",
                _id=visit.id_base_visit,
                module_code="test",
            )
        )

        assert r.status_code == 200
        assert r.json == {"success": "Item is successfully deleted"}

        r = self.client.get(
            url_for(
                "monitorings.get_visit_by_id",
                module_code="test",
                id=visit.id_base_visit,
            )
        )
        assert r.status_code == 404

    def test_delete_visit_not_found(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.delete(
            url_for("monitorings.delete_visit", _id=999999999, module_code="test")
        )

        assert r.status_code == 404
