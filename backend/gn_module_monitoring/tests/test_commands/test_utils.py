import pytest

from pathlib import Path

from gn_module_monitoring.tests.fixtures.generic import *
from gn_module_monitoring.command.imports.constant import FORBIDDEN_SQL_INSTRUCTION
from gn_module_monitoring.command.sql import execute_sql_file


@pytest.mark.usefixtures("client_class")
class TestCommandsUtils:
    def test_execute_sql_file(self):
        file_dir = Path(__file__).absolute().parent.parent / "fixtures"
        file_name = "bad_sql_forbidden.sql"

        with pytest.raises(Exception) as excinfo:
            execute_sql_file(file_dir, file_name, "module_code", FORBIDDEN_SQL_INSTRUCTION)

        assert (
            str(excinfo.value)
            == "erreur dans le script module_code instruction sql non autorisée bad_sql_forbidden.sql"
        )

        file_name = "bad_sql_error.sql"
        with pytest.raises(Exception) as excinfo:
            execute_sql_file(file_dir, file_name, "module_code", FORBIDDEN_SQL_INSTRUCTION)

        assert "erreur dans le script bad_sql_error.sql" in str(excinfo.value)
