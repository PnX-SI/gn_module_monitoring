import pytest
from marshmallow import ValidationError

from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.stores.type import GeometryStore
from gn_module_monitoring.tools.utils import schema_context


def make_geometry_store():
    with schema_context(entity=ENTITY_MAP["site"], field_name="geom"):
        return GeometryStore({})


def test_geometry_store_defaults_to_geojson():
    store = make_geometry_store()
    assert store.get_input_format() == "geojson"


def test_geojson_input_by_default():
    field = make_geometry_store().get_field()
    result = field.deserialize({"type": "Point", "coordinates": [43, 24]})
    assert result is not None


def test_wkt_string_rejected_by_default():
    field = make_geometry_store().get_field()
    with pytest.raises(ValidationError):
        field.deserialize("POINT(43 24)")


def test_wkt_input_with_schema_context():
    store = make_geometry_store()
    field = store.get_field()
    with schema_context(geometry_format="wkt"):
        assert store.get_input_format() == "wkt"
        result = field.deserialize("POINT(43 24)")
    assert result is not None


def test_wkt_context_does_not_accept_geojson_dict():
    store = make_geometry_store()
    field = store.get_field()
    with schema_context(geometry_format="wkt"):
        with pytest.raises(ValidationError):
            field.deserialize({"type": "Point", "coordinates": [43, 24]})


def test_wkt_with_srid_is_converted_to_4326():
    from geoalchemy2.shape import to_shape
    from pyproj import Transformer

    store = make_geometry_store()
    field = store.get_field()
    # Lambert 93 (2154) -> coordonnées attendues en 4326 (calculées indépendamment)
    x, y = 652000, 6862000
    lon, lat = Transformer.from_crs(2154, 4326, always_xy=True).transform(x, y)
    with schema_context(geometry_format="wkt;SRID=2154"):
        result = to_shape(field.deserialize(f"POINT({x} {y})"))
    assert result.x == pytest.approx(lon, abs=1e-6)
    assert result.y == pytest.approx(lat, abs=1e-6)


def test_unknown_geometry_format_is_rejected():
    store = make_geometry_store()
    with schema_context(geometry_format="kml"):
        with pytest.raises(ValueError):
            store.get_input_format()
