import pytest
from flask import url_for


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestRouteConfig:
    def test_get_config(self):
        response = self.client.get(url_for("monitorings.get_config_api"))
        assert response.json["default_display_field_names"]["area"] == "area_name"
