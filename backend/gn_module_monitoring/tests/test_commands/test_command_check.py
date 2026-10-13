from pathlib import Path

import pytest
from flask import current_app

from gn_module_monitoring.command import utils as command_utils
from gn_module_monitoring.command.cmd import cmd_check
from gn_module_monitoring.config import utils as config_utils

PROTOCOLS_DIR = Path(__file__).parent.parent / "protocols"


class TestCheckCommand:
    @pytest.fixture
    def protocols_dir(self, monkeypatch):
        monkeypatch.setattr(config_utils, "SUB_MODULE_CONFIG_DIR", PROTOCOLS_DIR)
        monkeypatch.setattr(command_utils, "SUB_MODULE_CONFIG_DIR", PROTOCOLS_DIR)
        return PROTOCOLS_DIR

    def test_check_test_protocol(self, protocols_dir):
        runner = current_app.test_cli_runner()
        result = runner.invoke(cmd_check, ["test_check"])
        assert result.exit_code == 0
        assert "Aucune anomalie détectée" in result.output
