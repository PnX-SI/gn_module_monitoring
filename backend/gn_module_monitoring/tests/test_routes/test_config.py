import pytest
from flask import url_for

from gn_module_monitoring.tests.fixtures.generic import *
from pypnusershub.tests.utils import set_logged_user_cookie


@pytest.mark.usefixtures("client_class")
class TestRouteConfig:
    def test_get_config(self):
        response = self.client.get(url_for("monitorings.get_config_api"))

        assert response.json["default_display_field_names"]["area"] == "area_name"

    def test_get_config_module(self, install_module_test, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        response = self.client.get(url_for("monitorings.get_config_api", module_code="test"))

        module_type_site = response.json["module"]["types_site"]
        type_site_name = [v["name"] for k, v in module_type_site.items()]

        assert set(type_site_name) == set(["Test_Grotte", "Test_Mine"])
        for id, type_site in module_type_site.items():
            assert set(type_site["display_properties"]).issubset(
                [k for k in response.json["site"]["specific"]]
            )
