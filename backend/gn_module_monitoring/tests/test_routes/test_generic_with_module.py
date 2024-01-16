import pytest
from flask import url_for

from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user_cookie

from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)

from gn_module_monitoring.tests.fixtures.generic import *
from gn_module_monitoring.monitoring.models import TMonitoringModules


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
        # TODO pb vue non touvée
        # response = self.client.get(
        #     url_for("monitorings.export_all_observations", module_code="test", method="sites")
        # )

        # expected_headers_content_type = "text/plain"
        # expected = '"base_site_code";"longitude";"latitude"'

        # assert response.status_code == 200
        # assert response.headers.get("content-type") == expected_headers_content_type
        # assert expected in response.text
