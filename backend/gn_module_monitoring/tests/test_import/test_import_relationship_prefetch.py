import numpy as np
import pandas as pd
import pytest
from marshmallow import EXCLUDE
from sqlalchemy import event

from geonature.utils.env import db
from gn_module_monitoring.modules import get_module
from gn_module_monitoring.monitoring.import_actions.actions import (
    EXTENDED_SCHEMA_EXCLUDE,
    prefetch_relationships,
)
from gn_module_monitoring.monitoring.import_actions.rows import build_schema_rows
from gn_module_monitoring.tools.stores.relationships.cache import CACHE_CONTEXT_KEY
from gn_module_monitoring.tools.utils import schema_context

# Identifiants absents de la base de test : chaque lecture non cachée va en base
ABSENT_CD_NOM = [900_000_000 + i for i in range(20)]
TAXREF_TABLE = "taxonomie.taxref"


@pytest.fixture
def observation():
    return get_module("demo").entities["observation"]


@pytest.fixture
def statements():
    captured = []

    def record(conn, cursor, statement, params, context, executemany):
        captured.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        yield captured
    finally:
        event.remove(db.engine, "before_cursor_execute", record)


def _schema(observation):
    return observation.get_extended_schema()(
        unknown=EXCLUDE,
        load_instance=False,
        only=["+data"],
        exclude=EXTENDED_SCHEMA_EXCLUDE["observation"] + ("id_digitiser",),
    )


def _rows(observation):
    df = pd.DataFrame(
        {
            "o__cd_nom": ABSENT_CD_NOM,
            "o__demo_observation_ok": [True] * len(ABSENT_CD_NOM),
            "o__demo_count": [1] * len(ABSENT_CD_NOM),
        }
    )
    return build_schema_rows(df, "observation", observation)


def _validate(schema, rows, cache=None):
    context = {CACHE_CONTEXT_KEY: cache} if cache is not None else {}
    with schema_context(geometry_format="wkt", **context):
        return [schema.validate(row) for row in rows]


def _count(statements, table):
    return sum(table in statement for statement in statements)


def test_prefetch_issues_one_query_per_model(observation, statements):
    rows = _rows(observation)
    statements.clear()
    prefetch_relationships(
        observation,
        rows,
        EXTENDED_SCHEMA_EXCLUDE["observation"] + ("id_digitiser",),
    )
    assert _count(statements, TAXREF_TABLE) == 1


def test_cache_reduces_queries_on_taxref(observation, statements):
    schema = _schema(observation)
    rows = _rows(observation)
    excluded = EXTENDED_SCHEMA_EXCLUDE["observation"] + ("id_digitiser",)

    # Sans cache : une lecture en base par ligne (la clé absente n'est jamais mise en cache)
    statements.clear()
    errors_without_cache = _validate(schema, rows)
    queries_without_cache = _count(statements, TAXREF_TABLE)

    # Avec cache : une seule requête de pré-chargement, puis aucune lecture pendant la validation
    statements.clear()
    cache = prefetch_relationships(observation, rows, excluded)
    errors_with_cache = _validate(schema, rows, cache)
    queries_with_cache = _count(statements, TAXREF_TABLE)

    assert queries_without_cache == len(rows)
    assert queries_with_cache == 1
    # Le cache ne change pas le résultat de la validation
    assert errors_with_cache == errors_without_cache
    assert all("cd_nom" in messages for messages in errors_with_cache)
