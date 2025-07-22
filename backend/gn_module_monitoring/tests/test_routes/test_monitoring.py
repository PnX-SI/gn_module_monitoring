import pytest
from flask import url_for

from geonature.utils.env import db
from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)

from io import StringIO
import pandas as pd
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class")
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

    def test_get_export_csv(self, install_module_test, monitorings_users, sites):
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
