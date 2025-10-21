import pytest
from flask import url_for

from gn_module_monitoring.tests.fixtures.generic import *
from pypnusershub.tests.utils import set_logged_user_cookie


@pytest.mark.usefixtures("client_class")
class TestRouteConfig:
    @pytest.mark.parametrize(
        "route", ["monitorings.get_config_api", "monitorings.get_config_apiV2"]
    )  # TODO remove when new config API is official
    def test_get_config(self, route):
        response = self.client.get(url_for(route))
        assert response.json["default_display_field_names"]["area"] == "area_name"

    @pytest.mark.parametrize(
        "route,fields_key",
        [("monitorings.get_config_api", "specific"), ("monitorings.get_config_apiV2", "fields")],
    )  # TODO remove when new config API is official
    def test_get_config_module(self, install_module_test, users,route,fields_key):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(url_for(route, module_code="test"))

        module_type_site = response.json["module"]["types_site"]
        type_site_name = [v["name"] for k, v in module_type_site.items()]

        assert set(type_site_name) == set(["Test_Grotte", "Test_Mine"])
        for id, type_site in module_type_site.items():
            assert set(type_site["display_properties"]).issubset(
                [k for k in response.json["site"][fields_key]]
            )
