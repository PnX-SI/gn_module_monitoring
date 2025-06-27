import pytest

from flask import url_for, current_app

from sqlalchemy import select

from geonature.utils.env import DB

from gn_module_monitoring.tests.fixtures.generic import *
from gn_module_monitoring.command.cmd import (
    cmd_remove_monitoring_module_cmd,
    cmd_process_sql,
    cmd_process_available_permission_module,
    cmd_add_module_nomenclature_cli,
    synchronize_synthese,
)
from gn_module_monitoring.monitoring.models import TMonitoringModules


@pytest.mark.usefixtures("client_class")
class TestCommands:
    def test_install_monitoring_module(self, install_module_test):
        # Installation du module
        # Test Installation
        result = DB.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        ).scalar_one()
        assert result.module_code == "test"

    def test_remove_monitoring_module(self, install_module_test):
        runner = current_app.test_cli_runner()

        # Suppression du module de test
        result = runner.invoke(cmd_remove_monitoring_module_cmd, ["test"])

        # Test suppression
        result = DB.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        ).scalar_one_or_none()
        assert result == None

    def test_process_all_with_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_sql, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0

    def test_process_all_without_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_sql)
        # Pas de result
        assert result.exit_code == 0

    def test_process_all_with_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        # import pdb
        result = runner.invoke(cmd_process_sql, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0

    def test_process_available_permission_module_without_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_available_permission_module)
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "Création des permissions pour test" in result.output

    def test_process_available_permission_module_with_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_available_permission_module, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "Création des permissions pour test" in result.output

    def test_process_available_permission_module_bad_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_available_permission_module, ["bad_module"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "le module n'existe pas" in result.output

    def test_cmd_add_module_nomenclature_cli(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_add_module_nomenclature_cli)
        # Pas de result juste <Result okay>
        assert result.exit_code == 2
        assert "Missing argument 'MODULE_CODE'" in result.output

    def test_cmd_add_module_nomenclature_cli(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande add_module_nomenclature
        result = runner.invoke(cmd_add_module_nomenclature_cli, ["test"])
        # Pas de result juste <Result okay>
        assert result.exit_code == 0
        assert "nomenclature type TEST_METEO - Météo - already exist" in result.output
        assert "nomenclature METEO_M - Mauvais temps - updated" in result.output
        assert 'probleme de type avec mnemonique="TEST_UNKWONW_TYPE"' in result.output

    def test_synchronize_synthese(self, install_module_test):
        # Installation du module
        # Test de la synchronisation synthese
        # Permet de tester la bonne execution du fichier synthese.sql
        runner = current_app.test_cli_runner()
        result = runner.invoke(synchronize_synthese, ["test"])
        assert result.exit_code == 0
