import pytest
from flask import url_for, current_app

from pypnusershub.tests.utils import set_logged_user_cookie
from geonature.tests.test_users_menu import tlist
from geonature.utils.env import db
from sqlalchemy import select

from gn_module_monitoring.monitoring.models import TMonitoringModules

# Liste des clés de premier niveau retournée par la config d'un module
CONFIG_KEYS = (
    "custom",
    "data",
    "default_display_field_names",
    "display_field_names",
    "module",
    "observation",
    "site",
    "sites_group",
    "synthese",
    "tree",
    "visit",
)


@pytest.fixture
def module_list(install_module_test, tlist):
    """
    Ajout d'une liste d'observateur au module de test
    """
    with db.session.begin_nested():
        module = db.session.scalar(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        )
        module.id_list_observer = tlist.id_liste
        db.session.add(module)
    return (module, tlist)


from gn_module_monitoring.monitoring.models import TMonitoringModules
from geonature.utils.env import db
from sqlalchemy import select

# Liste des clés de premier niveau retournée par la config d'un module
CONFIG_KEYS = (
    "custom",
    "data",
    "default_display_field_names",
    "display_field_names",
    "module",
    "observation",
    "site",
    "sites_group",
    "synthese",
    "tree",
    "visit",
)


@pytest.fixture
def module_list(install_module_test, tlist):
    """
    Ajout d'une liste d'observateur au module de test
    """
    with db.session.begin_nested():
        module = db.session.scalar(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        )
        module.id_list_observer = tlist.id_liste
        db.session.add(module)
    return (module, tlist)


@pytest.mark.usefixtures("client_class")
class TestRouteConfig:

    def test_get_config(self):
        response = self.client.get(url_for("monitorings.get_config_api"))

        assert response.json["default_display_field_names"]["area"] == "area_name"

    def test_get_config_generic(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(url_for("monitorings.get_config_api", module_code="generic"))
        data = response.json
        # Test éléments de premier niveau de la réponse
        assert set(CONFIG_KEYS) == set(data.keys())

        # Test niveau custom contienne à minima l'entré nomenclature
        assert "nomenclature" in data["data"].keys()

        # Test liste des observateurs
        assert "CODE_OBSERVERS_LIST" in data["custom"].keys()
        assert data["custom"]["CODE_OBSERVERS_LIST"] == current_app.config["MONITORINGS"].get(
            "CODE_OBSERVERS_LIST", {}
        )

    def test_get_config_module(self, module_list, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        module, tlist = module_list

        response = self.client.get(url_for("monitorings.get_config_api", module_code="test"))
        data = response.json

        # test éléments de premier niveau de la réponse
        assert set(CONFIG_KEYS) == set(data.keys())

        # Test liste des observateurs
        assert "CODE_OBSERVERS_LIST" in data["custom"].keys()
        assert data["custom"]["CODE_OBSERVERS_LIST"] == tlist.code_liste

        module_type_site = data["module"]["types_site"]
        type_site_name = [v["name"] for k, v in module_type_site.items()]

        assert set(type_site_name) == set(["Test_Grotte", "Test_Mine"])
        for id, type_site in module_type_site.items():
            assert set(type_site["display_properties"]).issubset(
                [k for k in data["site"]["specific"]]
            )
