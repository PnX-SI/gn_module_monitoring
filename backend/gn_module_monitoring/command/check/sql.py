from difflib import unified_diff

import click
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.dialects import postgresql
from psycopg2.errors import UndefinedTable
from pglast import prettify
from pglast.stream import RawStream
from pglast.ast import ViewStmt, DropStmt
from pglast.parser import parse_sql, fingerprint, ParseError

from geonature.utils.env import db

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.command.check.utils import wrap_errors


def find_sql_files(module_path):
    for filename in ["synthese.sql", "export.sql"]:
        yield module_path / filename
    for filepath in (module_path / "exports" / "csv").glob("*.sql"):
        yield filepath


def check_module_sql_view(module_code, fix, stmt):
    """
    Cette fonction compare le code de la vue définie dans le fichier avec le code de la vue existant en base.
    En cas de divergances, un diff est affiché.
    """
    viewname = f"{stmt.view.schemaname}.{stmt.view.relname}"
    try:
        viewdef = db.session.execute(sa.select(func.pg_get_viewdef(viewname))).scalar()
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            yield f"La vue '{viewname}' n’existe pas"
            if fix:
                yield f"\nPour corriger, lancer la commande 'geonature monitorings process_sql {module_code}'"
            return
        else:
            raise

    # As postgres do some rewrite of the view when it is created, the most robust way to compare
    # an existing view with a sql file is to execute the sql file to create a temporary view,
    # and compare their definitions.
    stmt.view.relname = f"{stmt.view.relname}_tmp"
    stmt.replace = False
    temporary_view = RawStream()(stmt)
    savepoint = db.session.begin_nested()
    try:
        db.session.execute(sa.text(temporary_view))
        tmp_viewdef = db.session.execute(
            sa.select(func.pg_get_viewdef(f"{stmt.view.schemaname}.{stmt.view.relname}"))
        ).scalar()
    finally:
        savepoint.rollback()
    if fingerprint(viewdef) != fingerprint(tmp_viewdef):
        yield (
            f"La vue {viewname} n’est pas à jour\n"
            + "\n".join(
                unified_diff(prettify(viewdef).splitlines(), prettify(tmp_viewdef).splitlines())
            )
        )
        if fix:
            yield f"\nPour corriger, lancer la commande 'geonature monitorings process_sql {module_code}'"


def check_module_sql_file(module_code, check_data, fix, sql_content):
    # Remplacement des paramètres sqlalchemy (:module_code)
    sql_content = sa.text(sql_content)
    if "module_code" in sql_content._bindparams:
        sql_content = sql_content.bindparams(module_code=module_code)
    sql_content = sql_content.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    # Le fichier est parsé avec la même lib que postgres
    try:
        ast = parse_sql(str(sql_content))
    except ParseError as e:
        yield e
        return

    expected_view_name = None
    for _ast in ast:
        stmt = _ast.stmt
        # On attend que des instructions DROP VIEW ou CREATE VIEW
        if isinstance(stmt, DropStmt):
            assert len(stmt.objects) == 1  # FIXME: yield error
            # Lors d’un DROP, on s’attend à ce que le CREATE VIEW suivant re-crée la vue du même nom
            expected_view_name = stmt.objects[0]
        elif isinstance(stmt, ViewStmt):
            if expected_view_name:
                if stmt.view.schemaname != expected_view_name[0].sval:
                    yield f"Mauvais schéma - attendu : {expected_view_name[0].sval}, trouvé : {stmt.view.schemaname}"
                if stmt.view.relname != expected_view_name[1].sval:
                    yield f"Mauvais nom de vue - attendu : {expected_view_name[1].sval}, trouvé : {stmt.view.relname}"
            expected_view_name = None
            if check_data:
                yield from check_module_sql_view(module_code, fix, stmt)
        else:
            yield f"Mauvaise instruction - attendue : DROP VIEW ou CREATE VIEW, trouvée : {type(stmt).__name__}"
            continue


def check_module_sql_files(module_code, check_data, fix):
    total_error_count = 0
    module_path = monitoring_module_config_path(module_code)
    for sql_file_path in find_sql_files(module_path):
        if not sql_file_path.exists():
            continue
        total_error_count += wrap_errors(
            f"Fichier SQL '{sql_file_path.relative_to(module_path)}'",
            check_module_sql_file(module_code, check_data, fix, sql_file_path.read_text()),
        )
    return total_error_count
