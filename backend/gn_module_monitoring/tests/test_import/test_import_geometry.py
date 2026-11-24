"""
Géométrie des sites à l'import (monitoring/import_actions/geometry.py) : x/y -> WKT, parsing WKT,
bornes, format GeoJSON de ImportGeometryField. Les erreurs sont enregistrées par un remplaçant de
`report_error` (aucune écriture dans t_user_errors).
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from marshmallow import ValidationError

from geonature.core.imports.checks.dataframe import utils as dataframe_utils
from geonature.core.imports.checks.errors import ImportCodeError

from gn_module_monitoring.monitoring.import_actions.geometry import (
    ImportGeometryField,
    check_wkt_geometries,
    fill_wkt_from_xy,
)

WKT = SimpleNamespace(source_field="src_s__geom", dest_field="s__geom")
X = SimpleNamespace(source_field="src_s__x", dest_field=None)
Y = SimpleNamespace(source_field="src_s__y", dest_field=None)
GEOM_4326 = SimpleNamespace(source_field="src_s__geom", dest_field="s__geom")


@pytest.fixture
def errors(monkeypatch):
    recorded = []

    def fake_report_error(imprt, entity, df, error):
        recorded.append(error)
        return set()

    monkeypatch.setattr(dataframe_utils, "report_error", fake_report_error)
    return recorded


def _fill(df):
    return fill_wkt_from_xy(None, None, df, wkt_field=WKT, x_field=X, y_field=Y)


def test_xy_numeric_written_as_point_without_comma(errors):
    df = pd.DataFrame(
        {"src_s__geom": [None, ""], "src_s__x": ["2,5", 2.5], "src_s__y": ["44.1", 44.1]}
    )
    updated = _fill(df)
    assert updated == {"src_s__geom"}
    assert df["src_s__geom"].tolist()[0] == "POINT(2.500000000000 44.100000000000)"
    assert df["src_s__geom"].tolist()[1] == "POINT(2.500000000000 44.100000000000)"
    assert errors == []


def test_xy_written_point_is_valid_wkt(errors):
    from shapely import wkt

    df = pd.DataFrame({"src_s__geom": [np.nan], "src_s__x": ["-1,25"], "src_s__y": [" 47.0 "]})
    _fill(df)
    point = wkt.loads(df["src_s__geom"].iloc[0])
    assert (point.x, point.y) == pytest.approx((-1.25, 47.0))
    assert errors == []


def test_existing_wkt_is_not_overwritten_and_warns(errors):
    df = pd.DataFrame({"src_s__geom": ["POINT(1 2)"], "src_s__x": ["5"], "src_s__y": ["6"]})
    _fill(df)
    assert df["src_s__geom"].iloc[0] == "POINT(1 2)"
    assert [e["error_code"] for e in errors] == [ImportCodeError.MULTIPLE_GEO_INFO_WARNING]


def test_non_numeric_x_reports_type_error_and_no_wkt(errors):
    df = pd.DataFrame({"src_s__geom": [None], "src_s__x": ["abc"], "src_s__y": ["44"]})
    _fill(df)
    assert pd.isna(df["src_s__geom"].iloc[0])
    assert len(errors) == 1
    assert errors[0]["error_code"] == ImportCodeError.INVALID_NUMERIC
    assert errors[0]["column"] == "s__x"


def test_non_finite_y_reports_type_error_and_no_wkt(errors):
    df = pd.DataFrame({"src_s__geom": [None], "src_s__x": ["2"], "src_s__y": ["inf"]})
    _fill(df)
    assert pd.isna(df["src_s__geom"].iloc[0])
    assert errors[0]["error_code"] == ImportCodeError.INVALID_NUMERIC
    assert errors[0]["column"] == "s__y"


@pytest.mark.parametrize(
    "x, y",
    [
        ("", "44"),
        (None, "44"),
        (np.nan, "44"),
        ("2", ""),
        ("2", None),
        ("2", np.nan),
    ],
)
def test_blank_x_or_y_gives_no_wkt_and_no_error(errors, x, y):
    df = pd.DataFrame({"src_s__geom": [None], "src_s__x": [x], "src_s__y": [y]}, dtype=object)
    _fill(df)
    assert pd.isna(df["src_s__geom"].iloc[0])
    assert errors == []


def test_check_wkt_valid_from_file_srid_is_reprojected(errors):
    df = pd.DataFrame({"src_s__geom": ["POINT(700000 6600000)"]})
    updated = check_wkt_geometries(
        None, None, df, file_srid=2154, wkt_field=WKT, geom_4326_field=GEOM_4326
    )
    assert updated == {"s__geom"}
    assert errors == []
    # Reprojection SQL depuis le SRID du fichier (2154) vers 4326
    assert "ST_Transform" in str(df["s__geom"].iloc[0].compile())


def test_check_wkt_4326_file_is_not_reprojected(errors):
    df = pd.DataFrame({"src_s__geom": ["POINT(2 44)"]})
    check_wkt_geometries(None, None, df, file_srid=4326, wkt_field=WKT, geom_4326_field=GEOM_4326)
    assert errors == []
    assert "ST_Transform" not in str(df["s__geom"].iloc[0].compile())


def test_check_wkt_invalid_is_reported_and_has_no_geometry(errors):
    df = pd.DataFrame({"src_s__geom": ["POINT(1 2", "POINT(700000 6600000)"]})
    check_wkt_geometries(None, None, df, file_srid=2154, wkt_field=WKT, geom_4326_field=GEOM_4326)
    assert [e["error_code"] for e in errors] == [ImportCodeError.INVALID_WKT]
    assert errors[0]["invalid_rows"].index.tolist() == [0]
    assert pd.isna(df["s__geom"].iloc[0])
    assert df["s__geom"].iloc[1] is not None


def test_check_wkt_out_of_file_srid_bounding_box(errors):
    # Coordonnées de degrés lues comme du Lambert 93 : hors de l'emprise du SRID 2154
    df = pd.DataFrame({"src_s__geom": ["POINT(2 44)"]})
    check_wkt_geometries(None, None, df, file_srid=2154, wkt_field=WKT, geom_4326_field=GEOM_4326)
    assert [e["error_code"] for e in errors] == [ImportCodeError.GEOMETRY_OUT_OF_BOX]
    # Aucune ligne géométrique valide : la colonne 4326 n'est pas écrite
    assert "s__geom" not in df


def test_wkt_field_empty_string_is_missing_not_invalid(errors):
    df = pd.DataFrame({"src_s__geom": ["  "]})
    check_wkt_geometries(None, None, df, file_srid=4326, wkt_field=WKT, geom_4326_field=GEOM_4326)
    assert errors == []


def test_wkt_empty_geometry_is_invalid():
    field = ImportGeometryField(geometry_format="wkt")
    with pytest.raises(ValidationError):
        field.deserialize("POINT EMPTY")


def test_wkt_format_is_default_and_independent_of_schema():
    field = ImportGeometryField()
    assert field.geometry_format == "wkt"
    assert field.deserialize("POINT (1 2)").wkt == "POINT (1 2)"


def test_geojson_2d_accepted_and_stored_in_4326():
    field = ImportGeometryField(geometry_format="geojson")
    geom = field.deserialize({"type": "Point", "coordinates": [2.0, 44.0]})
    assert geom.srid == 4326


def test_geojson_3d_rejected():
    """Décision : la 3e dimension est rejetée en GeoJSON (comportement de GeometryField)."""
    field = ImportGeometryField(geometry_format="geojson")
    with pytest.raises(ValidationError):
        field.deserialize({"type": "Point", "coordinates": [2.0, 44.0, 10.0]})


def test_wkt_invalid_geometry_rejected_with_same_message_as_geojson():
    """Polygone en auto-intersection : parsable, mais invalide. Même message que le GeoJSON."""
    field = ImportGeometryField(geometry_format="wkt")
    with pytest.raises(ValidationError) as wkt_error:
        field.deserialize("POLYGON((0 0, 1 1, 1 0, 0 1, 0 0))")
    field = ImportGeometryField(geometry_format="geojson")
    with pytest.raises(ValidationError) as geojson_error:
        field.deserialize(
            {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}
        )
    assert wkt_error.value.messages == geojson_error.value.messages == ["Invalid geometry."]


def test_wkt_valid_polygon_accepted():
    field = ImportGeometryField(geometry_format="wkt")
    geom = field.deserialize("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))")
    assert geom.is_valid


def test_wkt_3d_rejected():
    """Décision : la 3e dimension est rejetée en WKT comme en GeoJSON (une seule règle à l'import)."""
    field = ImportGeometryField(geometry_format="wkt")
    with pytest.raises(ValidationError):
        field.deserialize("POINT Z (2 44 10)")


def test_invalid_geometry_format_rejected():
    with pytest.raises(ValueError):
        ImportGeometryField(geometry_format="kml")


def test_fields_to_cast_excludes_geometry_column_by_type_not_by_name():
    """Le filtre repose sur le type SQL de la colonne transitoire, pas sur le nom du champ."""
    import sqlalchemy as sa
    from geoalchemy2 import Geometry

    from gn_module_monitoring.monitoring.import_actions.actions import get_fields_to_cast

    transient = sa.Table(
        "tmp_geometry_cast",
        sa.MetaData(),
        sa.Column("s__geom", Geometry("GEOMETRY", 4326)),
        sa.Column("s__text", sa.String),
        sa.Column("s__geom_renamed", Geometry("GEOMETRY", 4326)),
    )
    fields = {
        # nom quelconque : seul le type de la colonne transitoire compte
        "any_name": SimpleNamespace(dest_field="s__geom_renamed"),
        "s__text": SimpleNamespace(dest_field="s__text"),
        "source_only": SimpleNamespace(dest_field=None),
        "not_in_table": SimpleNamespace(dest_field="absent"),
    }
    kept = get_fields_to_cast(fields, transient)
    assert set(kept) == {"s__text", "source_only", "not_in_table"}


def test_geom_local_column_name_is_derived_from_geometry_field():
    from gn_module_monitoring.command.imports.constant import geom_local_column_name

    assert geom_local_column_name("geom") == "geom_local"
    assert geom_local_column_name("geometry") == "geometry_local"
