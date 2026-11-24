"""
Champ géométrie unifié : `GeojsonSerializationField` (tools/geometry.py) est utilisé par le schéma
des sites / groupes de sites et par `GeometryStore`. Même entrée, même sortie, même rejet de la 3D.
"""

import json

import pytest
from geoalchemy2.shape import from_shape, to_shape
from marshmallow import ValidationError
from shapely.geometry import Point

from gn_module_monitoring.monitoring.schemas import (
    MonitoringSitesGroupsSchema,
    MonitoringSitesSchema,
)
from gn_module_monitoring.tools.geometry import GeojsonSerializationField
from gn_module_monitoring.tools.stores.type import GeometryStore
from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.modules.entities import ENTITY_MAP

POINT_2D = {"type": "Point", "coordinates": [2.0, 44.0]}
POINT_3D = {"type": "Point", "coordinates": [2.0, 44.0, 10.0]}
POLYGON_2D = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
}
POLYGON_3D = {
    "type": "Polygon",
    "coordinates": [[[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1], [0, 0, 1]]],
}


def same_geometry(a, b):
    return to_shape(a).equals_exact(to_shape(b), 0) and a.srid == b.srid


def make_geometry_store(config=None):
    with schema_context(entity=ENTITY_MAP["site"], field_name="geom"):
        return GeometryStore(config or {})


def store_field(config=None):
    return make_geometry_store(config).get_field()


def test_schema_and_store_use_the_same_field_class():
    assert isinstance(MonitoringSitesSchema._declared_fields["geom"], GeojsonSerializationField)
    assert isinstance(
        MonitoringSitesGroupsSchema._declared_fields["geom"], GeojsonSerializationField
    )
    assert isinstance(store_field(), GeojsonSerializationField)


@pytest.mark.parametrize(
    "value", [POINT_2D, POLYGON_2D, '{"type": "Point", "coordinates": [2, 44]}']
)
def test_2d_geojson_is_accepted_by_schema_and_store_with_same_result(value):
    schema_geom = GeojsonSerializationField().deserialize(value)
    store_geom = store_field().deserialize(value)
    assert same_geometry(schema_geom, store_geom)
    assert store_geom.srid == 4326


@pytest.mark.parametrize("value", [POINT_3D, POLYGON_3D])
def test_3d_geojson_is_rejected_by_schema_and_store(value):
    with pytest.raises(ValidationError, match="Unexpected third dimension."):
        GeojsonSerializationField().deserialize(value)
    with pytest.raises(ValidationError, match="Unexpected third dimension."):
        store_field().deserialize(value)


def test_3d_json_string_is_rejected():
    with pytest.raises(ValidationError, match="Unexpected third dimension."):
        GeojsonSerializationField().deserialize(json.dumps(POINT_3D))


@pytest.mark.parametrize(
    "value,message",
    [
        ({"type": "Polygon", "coordinates": []}, "Empty geometry."),
        (
            {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]},
            "Invalid geometry.",
        ),
        ("not json", "Geometry error"),
    ],
)
def test_invalid_geometries_are_rejected_with_the_shared_messages(value, message):
    with pytest.raises(ValidationError, match=message):
        GeojsonSerializationField().deserialize(value)
    with pytest.raises(ValidationError, match=message):
        store_field().deserialize(value)


def test_empty_value_is_none():
    assert GeojsonSerializationField(allow_none=True).deserialize(None) is None
    assert store_field().deserialize(None) is None


def test_shapely_and_wkb_inputs_are_accepted_by_store_field():
    point = Point(2, 44)
    expected = from_shape(point, srid=4326)
    assert same_geometry(store_field().deserialize(point), expected)
    # WKB brut (bytes) : même géométrie, en SRID 4326
    assert same_geometry(store_field().deserialize(point.wkb), expected)


def test_output_is_geojson_2d_for_schema_and_store():
    stored = from_shape(Point(2, 44), srid=4326)
    expected = {"type": "Point", "coordinates": [2.0, 44.0]}
    assert GeojsonSerializationField().serialize("geom", {"geom": stored}) == expected
    assert store_field().serialize("geom", {"geom": stored}) == expected
