import pytest
from flask import url_for

from geonature.utils.env import db

from io import StringIO
import pandas as pd
from pypnusershub.tests.utils import set_logged_user_cookie
from gn_module_monitoring.tests.fixtures.generic import add_user_permission


@pytest.mark.usefixtures("client_class")
class TestModules:

    def test_get_fake_export_csv(self, install_module_test, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        # Add user permission for export
        add_user_permission(
            "test",
            users["admin_user"],
            scope=3,
            type_code_object="MONITORINGS_MODULES",
            code_action="E",
        )

        # test unauthorized
        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="inexistant")
        )
        assert response.status_code == 404

    def test_get_export_csv(self, install_module_test, users, sites):
        set_logged_user_cookie(self.client, users["admin_user"])

        # test unautorized
        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="sites")
        )
        assert response.status_code == 403

        # Add user permission for export
        add_user_permission(
            "test",
            users["admin_user"],
            scope=3,
            type_code_object="MONITORINGS_MODULES",
            code_action="E",
        )

        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="sites")
        )

        assert response.status_code == 200
        expected_headers_content_type = "text/plain"
        assert response.headers.get("content-type") == expected_headers_content_type

        expected_columns = ["base_site_code", "longitude", "latitude"]
        csv_content = pd.read_csv(StringIO(response.data.decode("utf-8")), sep=";")

        # test columns
        columns = list(csv_content.columns)
        assert columns == expected_columns

        # test data is not empty
        assert csv_content.empty == False


@pytest.fixture
def visit_module_test(install_module_test, sites, datasets):
    from datetime import date

    from sqlalchemy import select

    from gn_module_monitoring.monitoring.models import TMonitoringModules, TMonitoringVisits

    module = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one()
    visit = TMonitoringVisits(
        id_base_site=list(sites.values())[0].id_base_site,
        id_module=module.id_module,
        id_dataset=datasets["orphan_dataset"].id_dataset,
        visit_date_min=date(2025, 1, 1),
    )
    with db.session.begin_nested():
        db.session.add(visit)
    return visit


# TODO: To delete once the old API is completely removed and the new API is fully functional.
@pytest.mark.usefixtures("client_class")
class TestOldApiWithNewConfig:
    """Les routes de l'ancienne API encore utilisées par l'interface reposent sur get_config"""

    def test_breadcrumbs_keep_config_cache(self, visit_module_test, users):
        from gn_module_monitoring.config.repositories import get_config

        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.breadcrumbs_object_api",
                module_code="test",
                object_type="visit",
                id=visit_module_test.id_base_visit,
            )
        )
        assert r.status_code == 200, r.json
        assert r.json[-1]["object_type"] == "visit"
        assert r.json[-1]["id"] == visit_module_test.id_base_visit

        # La config en cache est toujours au format de get_config
        assert "fields" in get_config("test")["visit"]

    def test_list_object(self, visit_module_test, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for("monitorings.list_object_api", module_code="test", object_type="visit")
        )
        assert r.status_code == 200, r.json
        assert visit_module_test.id_base_visit in [v["id_base_visit"] for v in r.json]

    def test_delete_object(self, visit_module_test, users):
        from gn_module_monitoring.monitoring.models import TMonitoringVisits

        set_logged_user_cookie(self.client, users["admin_user"])
        id_visit = visit_module_test.id_base_visit
        r = self.client.delete(
            url_for(
                "monitorings.legacy.delete_object_api",
                module_code="test",
                object_type="visit",
                id=id_visit,
            )
        )
        assert r.status_code == 200, r.json
        db.session.expire_all()
        assert db.session.get(TMonitoringVisits, id_visit) is None

    def test_breadcrumbs_with_parents_path(self, visit_module_test, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.breadcrumbs_object_api",
                module_code="test",
                object_type="visit",
                id=visit_module_test.id_base_visit,
                parents_path=["module", "site"],
            )
        )
        assert r.status_code == 200, r.json
        assert [b["object_type"] for b in r.json] == ["module", "site", "visit"]
        assert r.json[1]["id"] == visit_module_test.id_base_site
        assert r.json[2]["params"] == {"parents_path": ["module", "site"]}

    def test_breadcrumbs_create_object(self, visit_module_test, users):
        # Page de création : pas d'id, le parent est donné dans les paramètres
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.breadcrumbs_object_api",
                module_code="test",
                object_type="visit",
                parents_path=["module", "site"],
                id_base_site=visit_module_test.id_base_site,
            )
        )
        assert r.status_code == 200, r.json
        assert [b["object_type"] for b in r.json] == ["module", "site"]

    def test_update_synthese(self, install_module_test, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.post(url_for("monitorings.update_synthese_api", module_code="test"))
        # La synthèse n'est pas activée dans la config du module test : pas de synchronisation
        assert r.status_code == 204

    def test_export_pdf(self, install_module_test, sites, users, monkeypatch):
        import gn_module_monitoring.routes.monitoring as routes_monitoring

        add_user_permission(
            "test",
            users["admin_user"],
            scope=3,
            type_code_object="MONITORINGS_MODULES",
            code_action="E",
        )
        captured = {}

        def fake_generate_pdf(template, data):
            captured["template"] = template
            captured["data"] = data
            return b"%PDF"

        monkeypatch.setattr(routes_monitoring.fm, "generate_pdf", fake_generate_pdf)

        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]
        r = self.client.post(
            url_for(
                "monitorings.post_export_pdf",
                module_code="test",
                object_type="site",
                id=site.id_base_site,
            ),
            json={"template": "fiche_site.html", "map": "", "extra_data": {}},
        )
        assert r.status_code == 200
        monitoring_object = captured["data"]["monitoring_object"]
        assert monitoring_object["id"] == site.id_base_site
        assert monitoring_object["properties"]["base_site_name"] == site.base_site_name
        assert monitoring_object["properties"]["types_site"] == [
            t.nomenclature.label_fr for t in site.types_site
        ]
        assert monitoring_object["geometry"]["type"] == "Point"
