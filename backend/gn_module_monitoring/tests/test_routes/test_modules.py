import pytest

from flask import url_for
from sqlalchemy import select
from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user_cookie
from apptax.taxonomie.models import BibListes
from pypnusershub.db.models import UserList
from gn_module_monitoring.tests.fixtures.generic import add_user_permission
from gn_module_monitoring.tests.fixtures.module import install_monitoring_module

from gn_module_monitoring.monitoring.models import TMonitoringModules, TMonitoringVisits


@pytest.fixture
def module_test(types_site, users):
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


@pytest.mark.usefixtures("client_class")
class TestModules:

    def test_get_modules_api(self, users, module_test):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(url_for("monitorings.get_modules_api"))
        assert r.status_code == 200

    def test_get_modules_api_field_name(self, users, module_test):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_module_api",
                value=module_test.module_code,
                field_name="module_code",
            )
        )
        assert r.status_code == 200
        assert r.json["module_code"] == module_test.module_code

    def test_all_types_site_from_module_id(self, users, module_test):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_all_types_site_from_module_id",
                module_code=module_test.module_code,
            )
        )
        assert r.status_code == 200
        type_site = r.json[0]
        assert set(type_site.keys()) == set(["config", "id_nomenclature_type_site", "label"])

    def test_patch_module(self, module_test, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        data = {"taxonomy_display_field_name": "lb_nom", "id_module": module_test.id_module}

        r = self.client.patch(
            url_for(
                "monitorings.patch_module",
                module_code="test",
                _id=module_test.id_module,
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["taxonomy_display_field_name"] == data["taxonomy_display_field_name"]

    def test_patch_module_not_found(self, module_test, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        data = {"taxonomy_display_field_name": "lb_nom"}

        r = self.client.patch(
            url_for(
                "monitorings.patch_module",
                module_code="test",
                _id=999999999,
            ),
            json=data,
        )
        assert r.status_code == 404
