import pytest
import shutil

from pathlib import Path
from flask import url_for, current_app

from pypnusershub.tests.utils import set_logged_user_cookie

from sqlalchemy import select

from gn_module_monitoring.tests.fixtures.generic import *
from gn_module_monitoring.command.cmd import (
    cmd_remove_monitoring_module_cmd,
    cmd_process_all,
    cmd_process_export_csv,
    cmd_process_available_permission_module,
    cmd_add_module_nomenclature_cli,
)
from gn_module_monitoring.monitoring.models import TMonitoringModules
from geonature.utils.env import BACKEND_DIR, DB


@pytest.mark.usefixtures("client_class", "temporary_transaction")
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
        result = runner.invoke(cmd_process_all, ["test"])
        # Pas de result juste <Result okay>
        assert result
        result = runner.invoke(cmd_process_export_csv, ["test"])
        # Pas de result juste <Result okay>
        assert result

    def test_process_all_without_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        result = runner.invoke(cmd_process_all)
        # Pas de result
        assert result.exit_code == 0

        result = runner.invoke(cmd_process_export_csv)
        # Pas de result
        assert result.exit_code == 0

    def test_process_all_with_module(self, install_module_test):
        runner = current_app.test_cli_runner()
        # Commande process all
        # import pdb
        result = runner.invoke(cmd_process_all, ["test"])
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
