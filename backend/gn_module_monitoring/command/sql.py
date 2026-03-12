import os
from pathlib import Path

from gn_module_monitoring.command.imports.constant import FORBIDDEN_SQL_INSTRUCTION
from sqlalchemy import text

from geonature.utils.env import DB

from gn_module_monitoring.config.utils import (
    monitoring_module_config_path,
)


def process_sql_files(
    dir=None, module_code=None, depth=1, allowed_files=["export.sql", "synthese.sql"]
):
    sql_dir = Path(monitoring_module_config_path(module_code))
    if dir:
        sql_dir = sql_dir / "exports/csv"
    if not sql_dir.is_dir():
        return

    if not allowed_files:
        allowed_files = []
    count_depth = 0
    for root, dirs, files in os.walk(sql_dir, followlinks=True):
        count_depth = count_depth + 1
        for f in files:
            if not f.endswith(".sql"):
                continue
            if not f in allowed_files and allowed_files:
                continue
            # Vérification commandes non autorisée
            try:
                execute_sql_file(root, f, module_code, FORBIDDEN_SQL_INSTRUCTION)
                print("{} - exécution du fichier : {}".format(module_code, f))
            except Exception as e:
                print(e)

        # Limite profondeur de la recherche dans les répertoires
        if depth:
            if count_depth >= depth:
                break


def execute_sql_file(dir, file, module_code, forbidden_instruction=[]):
    """
    Execution d'un fichier sql dans la base de donnée
    dir : nom du répertoire
    file : nom du fichier à éxécuter
    module_code : code du module
    forbidden_instruction : liste d'instructions sql qui sont proscrites du fichier.

    """
    sql_content = Path(Path(dir) / file).read_text()
    for sql_cmd in forbidden_instruction:
        if sql_cmd.lower() in sql_content.lower():
            raise Exception(
                "erreur dans le script {} instruction sql non autorisée {}".format(
                    module_code, file, sql_cmd
                )
            )

    try:
        with DB.engine.begin() as conn:
            conn.execute(
                text(sql_content),
                module_code=module_code,
            )
    except Exception as e:
        raise Exception("{} - erreur dans le script {} : {}".format(module_code, file, e))
