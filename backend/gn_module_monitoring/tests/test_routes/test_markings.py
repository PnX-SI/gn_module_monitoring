from datetime import datetime

import pytest

from flask import url_for
from sqlalchemy import select

from pypnusershub.tests.utils import set_logged_user_cookie
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringMarkingEvent, TMonitoringModules


@pytest.fixture
def markings_routes(install_module_test_indi, nomenclature_type_markings):
    individuals = install_module_test_indi
    module = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test_indi")
    ).scalar_one()

    db_markings = []
    for individual in individuals:
        db_markings.append(
            TMonitoringMarkingEvent(
                id_individual=individual.id_individual,
                id_module=module.id_module,
                id_digitiser=individual.id_digitiser,
                id_operator=individual.id_digitiser,
                marking_date=datetime.strptime("2025-01-01", "%Y-%m-%d"),
                marking_location="Là bas",
                marking_code="0007",
                id_nomenclature_marking_type=nomenclature_type_markings.id_nomenclature,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_markings)
        db.session.flush()

    return db_markings


@pytest.mark.usefixtures("client_class")
class TestMarkings:

    def test_get_markings(self, markings_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_markings",
                module_code="test_indi",
            )
        )

        assert r.status_code == 200
        expected_markings = {marking.id_marking for marking in markings_routes}
        current_markings = {marking["id_marking"] for marking in r.json["items"]}
        assert expected_markings.issubset(current_markings)

    def test_get_markings_with_individual(self, markings_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        marking_instance = markings_routes[0]

        r = self.client.get(
            url_for(
                "monitorings.get_markings",
                module_code="test_indi",
                id_individual=marking_instance.id_individual,
            )
        )

        assert r.status_code == 200
        current_markings = {marking["id_marking"] for marking in r.json["items"]}
        assert marking_instance.id_marking in current_markings

    def test_get_marking_by_id(self, markings_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        marking_instance = markings_routes[0]

        r = self.client.get(
            url_for(
                "monitorings.get_marking_by_id",
                module_code="test_indi",
                id=marking_instance.id_marking,
            )
        )

        assert r.status_code == 200
        assert r.json["id_marking"] == marking_instance.id_marking
        assert r.json["marking_location"] == marking_instance.marking_location

    def test_get_marking_by_id_not_found(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for(
                "monitorings.get_marking_by_id",
                module_code="test_indi",
                id=999999999,
            )
        )

        assert r.status_code == 404

    def test_post_marking(self, markings_routes, users, nomenclature_type_markings):
        set_logged_user_cookie(self.client, users["admin_user"])
        marking_instance = markings_routes[0]

        data = {
            "id_individual": marking_instance.id_individual,
            "id_digitiser": users["admin_user"].id_role,
            "id_operator": users["admin_user"].id_role,
            "marking_date": "2025-06-01",
            "marking_location": "new_location",
            "marking_code": "new_code",
            "id_nomenclature_marking_type": nomenclature_type_markings.id_nomenclature,
        }

        r = self.client.post(
            url_for(
                "monitorings.post_marking",
                module_code="test_indi",
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_individual"] == data["id_individual"]
        assert r.json["marking_location"] == data["marking_location"]
        assert r.json["marking_code"] == data["marking_code"]

    def test_patch_marking(self, markings_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        marking_instance = markings_routes[0]

        data = {
            "id_marking": marking_instance.id_marking,
            "id_individual": marking_instance.id_individual,
            "id_digitiser": marking_instance.id_digitiser,
            "id_operator": marking_instance.id_operator,
            "marking_date": "2025-01-01",
            "marking_location": "updated_location",
            "marking_code": marking_instance.marking_code,
            "id_nomenclature_marking_type": marking_instance.id_nomenclature_marking_type,
        }

        r = self.client.patch(
            url_for(
                "monitorings.patch_marking",
                module_code="test_indi",
                _id=marking_instance.id_marking,
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_marking"] == marking_instance.id_marking
        assert r.json["marking_location"] == data["marking_location"]

    def test_patch_marking_not_found(self, markings_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.patch(
            url_for(
                "monitorings.patch_marking",
                module_code="test_indi",
                _id=999999999,
            ),
            json={},
        )

        assert r.status_code == 404

    def test_delete_marking(self, markings_routes, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        marking_instance = markings_routes[-1]

        r = self.client.delete(
            url_for(
                "monitorings.delete_marking",
                _id=marking_instance.id_marking,
                module_code="test_indi",
            )
        )

        assert r.status_code == 200
        assert r.json == {"success": "Item is successfully deleted"}

        r = self.client.get(
            url_for(
                "monitorings.get_marking_by_id",
                module_code="test_indi",
                id=marking_instance.id_marking,
            )
        )
        assert r.status_code == 404

    def test_delete_marking_not_found(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.delete(
            url_for("monitorings.delete_marking", _id=999999999, module_code="test_indi")
        )

        assert r.status_code == 404
