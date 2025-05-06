import pytest

from flask import url_for, current_app

from sqlalchemy import select

from geonature.utils.env import DB

from gn_module_monitoring.tests.fixtures.generic import *

from gn_module_monitoring.config.repositories import get_config


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestMonitoringObject:
    def test_process_synthese(self, install_module_test):
        """
        Test de la méthode `process_synthese` de`MonitoringObject`.

        Test que la méthode `process_synthese` de `MonitoringObject` fonctionne correctement
            avec l'objet site
            et sans erreur avec l'objet sites_group mais avec un logging approprié.

        TODO ajouter des données et vérifier que la table synthèse soit correctement peuplée
        """

        from gn_module_monitoring.monitoring.repositories import MonitoringObject

        module_code = "test"
        config = get_config(module_code, force=True)
        config["synthese"] = True

        object = MonitoringObject(module_code, "site", config, id=None, model=None)
        result = object.process_synthese()
        assert result == True

        config["synthese"] = True
        object = MonitoringObject(module_code, "sites_group", config, id=None, model=None)
        result = object.process_synthese()
        assert result == None
