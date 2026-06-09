import pytest
import json
from flask import url_for
from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user_cookie


@pytest.mark.usefixtures("client_class", "temporary_transaction")
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

        r = self.client.get(url_for("monitorings.get_visits", id_base_site=site.id_base_site))

        expected_visits = {
            visit.id_base_visit for visit in visits if visit.id_base_site == site.id_base_site
        }
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}

        assert expected_visits.issubset(current_visits)

    def _visit_post_data(self, user, site, dataset):
        return {
            "properties": {
                "comments": "new",
                "id_base_site": site.id_base_site,
                "id_base_visit": None,
                "id_dataset": dataset.id_dataset,
                "id_digitiser": user.id_role,
                "id_module": None,
                "medias": [],
                "nb_observations": None,
                "observers": [user.id_role],
                "observers_txt": None,
                "visit_date_max": "2026-4-17",
                "visit_date_min": "2026-4-17",
                "meteo": None,
            }
        }

    def _post_visit(self, user, dataset, site):
        post_data = self._visit_post_data(user, site, dataset)
        return self.client.post(
            url_for("monitorings.create_object_api", module_code="test", object_type="visit"),
            data=json.dumps(post_data),
            content_type="application/json",
        )

    def test_create_visit(self, users, install_module_test, datasets, sites):
        user = users["admin_user"]
        set_logged_user_cookie(self.client, user)
        site = list(sites.values())[0]
        dataset = datasets["orphan_dataset"]
        r = self._post_visit(user, dataset, site)

        assert r.status_code == 200

        dataset.acquisition_framework.opened = False
        db.session.flush()
        r = self._post_visit(user, dataset, site)
        assert r.status_code == 409

    def test_update_visit(self, users, install_module_test, datasets, sites):
        user = users["admin_user"]
        set_logged_user_cookie(self.client, user)
        site = list(sites.values())[0]
        dataset = datasets["orphan_dataset"]
        r = self._post_visit(user, dataset, site)
        assert r.status_code == 200
        visit_id = r.json["id"]
        post_data = self._visit_post_data(user, site, dataset)

        post_data["properties"]["comments"] = "updated"
        post_data["properties"]["id_base_visit"] = visit_id
        url = url_for(
            "monitorings.update_object_api",
            module_code="test",
            object_type="visit",
            id=visit_id,
        )
        r = self.client.patch(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
        )
        assert r.status_code == 200

        dataset.acquisition_framework.opened = False
        db.session.flush()
        r = self.client.patch(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
        )
        assert r.status_code == 409

    def test_delete_visit(self, users, install_module_test, datasets, sites):
        user = users["admin_user"]
        set_logged_user_cookie(self.client, user)
        dataset = datasets["orphan_dataset"]
        r = self._post_visit(user, dataset, list(sites.values())[0])
        visit_id = r.json["id"]
        url = url_for(
            "monitorings.delete_object_api",
            module_code="test",
            object_type="visit",
            id=visit_id,
        )
        dataset.acquisition_framework.opened = False
        db.session.flush()
        r = self.client.delete(url)
        assert r.status_code == 409
        dataset.acquisition_framework.opened = True
        db.session.flush()

        r = self.client.delete(url)
        assert r.status_code == 200
