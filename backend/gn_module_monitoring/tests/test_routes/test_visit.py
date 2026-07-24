from datetime import datetime

from gn_module_monitoring.tests.fixtures.module import install_monitoring_module
import pytest

from flask import current_app, url_for

from pypnusershub.tests.utils import set_logged_user_cookie
from geonature.utils.env import db, BACKEND_DIR
from gn_module_monitoring.monitoring.models import TMonitoringModules, TMonitoringVisits
from sqlalchemy import select

from apptax.taxonomie.models import BibListes
from pypnusershub.db.models import UserList


@pytest.fixture
def module_test_visit(types_site, users):
    install_monitoring_module("test", types_site, users)
    module_test = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one_or_none()

    with db.session.begin_nested():
        module_test.id_list_taxonomy = db.session.scalar(select(BibListes.id_liste).limit(1))
        module_test.id_list_observer = db.session.scalar(select(UserList.id_liste).limit(1))
        module_test.taxonomy_display_field_name = "nom_vern,lb_nom"
        db.session.add(module_test)

    return module_test


@pytest.fixture
def visits_routes(sites, datasets, module_test_visit):
    visit_date_min = datetime.strptime("2025-01-01", "%Y-%m-%d").date()
    dataset = datasets["orphan_dataset"]
    db_visits = []
    for site in sites.values():
        db_visits.append(
            TMonitoringVisits(
                id_base_site=site.id_base_site,
                id_module=module_test_visit.id_module,
                id_dataset=dataset.id_dataset,
                visit_date_min=visit_date_min,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_visits)
    db.session.flush()
    return db_visits


@pytest.mark.usefixtures("client_class", "visits_routes")
class TestVisits:

    def test_get_visits(self, visits_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_visits",
            )
        )

        expected_visits = {visit.id_base_visit for visit in visits_routes}
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}
        assert expected_visits.issubset(current_visits)
        assert all(visit["module"] is not None for visit in r.json["items"])

    def test_get_visits_with_site(self, visits_routes, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]

        r = self.client.get(
            url_for(
                "monitorings.get_visits",
                id_base_site=site.id_base_site,
            )
        )

        expected_visits = {
            visit.id_base_visit
            for visit in visits_routes
            if visit.id_base_site == site.id_base_site
        }
        current_visits = {visit["id_base_visit"] for visit in r.json["items"]}

        assert expected_visits.issubset(current_visits)

    def test_get_visit_by_id(self, visits_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = visits_routes[0]

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

    def test_post_visit(self, visits_routes, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]

        data = {
            "id_base_site": site.id_base_site,
            "visit_date_min": "2024-01-01",
            "id_dataset": visits_routes[0].id_dataset,
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

    def test_patch_visit(self, visits_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = visits_routes[0]

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

    def test_patch_visit_not_found(self, visits_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        module_code = "test"

        r = self.client.patch(
            url_for(
                "monitorings.patch_visit",
                module_code=module_code,
                _id=999999999,
            ),
            json={},
        )

        assert r.status_code == 404

    def test_delete_visit(self, visits_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = visits_routes[-1]

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
                object_type="visit",
            )
        )
        assert r.status_code == 404

    def test_delete_visit_not_found(self, visits_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.delete(
            url_for("monitorings.delete_visit", _id=999999999, module_code="test")
        )

        assert r.status_code == 404
