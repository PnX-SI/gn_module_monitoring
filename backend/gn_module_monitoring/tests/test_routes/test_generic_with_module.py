import pytest
from flask import url_for

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestModules:
    def test_get_export_csv(self, monitoring_module, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        response = self.client.get(
            url_for("monitorings.export_all_observations", module_code="test", method="sites")
        )

        expected_headers_content_type = "text/plain"
        expected = '"base_site_code";"longitude";"latitude"'

        assert response.status_code == 200
        assert response.headers.get("content-type") == expected_headers_content_type
        assert expected in response.text
