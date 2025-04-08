import pytest
from flask import url_for

from geonature.utils.env import db
from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.tests.fixtures.generic import *
from gn_module_monitoring.monitoring.models import TMonitoringModules, TMonitoringSites


def add_user_permission(module_code, user, scope, type_code_object, code_action="CRUVED"):
    module = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == module_code)
    ).scalar_one()
    actions = {
        code: db.session.execute(
            select(PermAction).where(PermAction.code_action == code)
        ).scalar_one()
        for code in code_action
    }
    with db.session.begin_nested():
        if scope > 0:
            object_all = db.session.scalars(
                select(PermObject).where(PermObject.code_object == type_code_object)
            ).all()
            for action in actions.values():
                for obj in object_all + module.objects:
                    permission = Permission(
                        role=user,
                        action=action,
                        module=module,
                        object=obj,
                        scope_value=scope if scope != 3 else None,
                        sensitivity_filter=None,
                    )
                    db.session.add(permission)


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestModules:
    def test_get_fake_export_csv(self, install_module_test, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        # Add user permission for export
        add_user_permission(
            "test",
            monitorings_users["admin_user"],
            scope=3,
            type_code_object="MONITORINGS_MODULES",
            code_action="E",
        )

        # test unauthorized
        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="inexistant")
        )
        assert response.status_code == 404

    def test_get_export_csv(self, install_module_test, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])

        # test unautorized
        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="sites")
        )
        assert response.status_code == 403

        # Add user permission for export
        add_user_permission(
            "test",
            monitorings_users["admin_user"],
            scope=3,
            type_code_object="MONITORINGS_MODULES",
            code_action="E",
        )

        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="sites")
        )

        expected_headers_content_type = "text/plain"
        expected = '"base_site_code";"longitude";"latitude"'

        assert response.status_code == 200
        assert response.headers.get("content-type") == expected_headers_content_type
        assert expected in response.text

    def test_delete_site_with_visits(self, sites, visits, monitorings_users):
        """
        Test de suppression interdite d'un site qui a des visites associées.
        """
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        # Choisir un site qui a au moins une visite (fixture visits crée une visite pour chaque site)
        site = list(sites.values())[0]
        id_base_site = site.id_base_site

        r = self.client.delete(
            url_for(
                "monitorings.delete_object_api",
                module_code="MONITORINGS",
                object_type="site",
                id=id_base_site,
            )
        )

        # Vérification que la suppression est interdite
        assert r.status_code == 403
        assert "cannot delete" in r.json.get("description", "").lower()

        # Vérifier que le site est toujours présent en base
        site_in_db = db.get_or_404(TMonitoringSites, id_base_site)
        assert site_in_db is not None
