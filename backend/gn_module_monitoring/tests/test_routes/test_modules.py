import pytest

from flask import url_for

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class")
class TestModules:

    def test_get_modules_api(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        add_user_permission(
            "MONITORINGS",
            users["admin_user"],
            scope=3,
            type_code_object="ALL",
            code_action="R",
        )
        r = self.client.get(url_for("monitorings.get_modules_api"))
        # TODO test response
        assert r.status_code == 200
