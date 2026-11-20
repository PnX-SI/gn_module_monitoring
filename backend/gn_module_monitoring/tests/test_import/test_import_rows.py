import datetime
from marshmallow import EXCLUDE

import numpy as np
import pandas as pd
import pytest

from gn_module_monitoring.modules import get_module
from gn_module_monitoring.monitoring.import_actions.rows import build_schema_rows


@pytest.fixture
def observation():
    return get_module("demo").entities["observation"]


def test_absent_values_become_none(observation):
    df = pd.DataFrame(
        {
            "o__comments": [np.nan, pd.NA, "", None, "texte"],
            "o__demo_count": [pd.NA, np.nan, None, "", 2],
        }
    )
    rows = build_schema_rows(df, "observation", observation)
    assert rows == [
        {"comments": None, "demo_count": None},
        {"comments": None, "demo_count": None},
        {"comments": None, "demo_count": None},
        {"comments": None, "demo_count": None},
        {"comments": "texte", "demo_count": 2},
    ]


def test_missing_date_becomes_none_and_dates_are_native(observation):
    df = pd.DataFrame(
        {
            "o__comments": [
                pd.NaT,
                pd.Timestamp("2026-03-04"),
                datetime.date(2026, 5, 6),
            ],
        }
    )
    rows = build_schema_rows(df, "observation", observation)
    assert rows[0]["comments"] is None
    assert rows[1]["comments"] == datetime.datetime(2026, 3, 4)
    assert type(rows[1]["comments"]) is datetime.datetime
    assert rows[2]["comments"] == datetime.date(2026, 5, 6)


def test_integer_read_as_float_keeps_its_value(observation):
    # Une colonne d'entiers avec une valeur absente est lue en float par pandas
    df = pd.DataFrame({"o__demo_count": [3.0, np.nan, 0.0]})
    rows = build_schema_rows(df, "observation", observation)
    assert [row["demo_count"] for row in rows] == [3, None, 0]
    assert type(rows[0]["demo_count"]) is int


def test_numpy_scalars_become_python_values(observation):
    df = pd.DataFrame(
        {
            "o__demo_count": np.array([7, 8], dtype=np.int64),
            "o__demo_observation_ok": np.array([True, False], dtype=np.bool_),
        }
    )
    rows = build_schema_rows(df, "observation", observation)
    assert rows == [
        {"demo_count": 7, "demo_observation_ok": True},
        {"demo_count": 8, "demo_observation_ok": False},
    ]
    assert type(rows[0]["demo_count"]) is int
    assert type(rows[0]["demo_observation_ok"]) is bool


def test_additional_fields_are_flat(observation):
    # Champs supplémentaires (non natifs) : passés à plat, comme l'API ; le schéma les range
    # dans `data`.
    df = pd.DataFrame(
        {
            "o__cd_nom": [100],
            "o__demo_count": [2],
            "o__demo_stade": [12],
        }
    )
    rows = build_schema_rows(df, "observation", observation)
    assert rows == [{"cd_nom": 100, "demo_count": 2, "demo_stade": 12}]


def test_absent_column_produces_no_key(observation):
    df = pd.DataFrame({"o__comments": ["texte"]})
    rows = build_schema_rows(df, "observation", observation)
    assert rows == [{"comments": "texte"}]


def test_ignored_field_is_excluded(observation):
    # id_observation est généré à l'import : une colonne de ce nom ne produit aucune clé
    df = pd.DataFrame({"id_observation": [42], "o__comments": ["texte"]})
    rows = build_schema_rows(df, "observation", observation)
    assert rows == [{"comments": "texte"}]


def test_rows_follow_dataframe_index_order(observation):
    df = pd.DataFrame({"o__comments": ["a", "b"]}, index=[5, 7])
    rows = build_schema_rows(df, "observation", observation)
    assert rows == [{"comments": "a"}, {"comments": "b"}]
    assert list(df.index) == [5, 7]


def test_empty_dataframe_gives_no_rows(observation):
    df = pd.DataFrame({"o__comments": pd.Series([], dtype=object)})
    assert build_schema_rows(df, "observation", observation) == []


def test_row_is_validated_by_extended_schema(observation):
    schema = observation.get_extended_schema()(
        unknown=EXCLUDE, load_instance=False, only=["+data"]
    )
    df = pd.DataFrame(
        {
            "o__cd_nom": [100, 100, np.nan],
            "o__demo_observation_ok": [True, True, True],
            "o__demo_count": [2, 0, 1],
        }
    )
    rows = build_schema_rows(df, "observation", observation)

    assert schema.validate(rows[0]) == {}
    # validate_cel de l'entité : une observation validée doit avoir au moins un individu
    assert schema.validate(rows[1]) == {
        "_schema": ["Une observation validée doit avoir au moins un individu."]
    }
    # cd_nom requis, absent de la ligne
    assert "cd_nom" in schema.validate(rows[2])
