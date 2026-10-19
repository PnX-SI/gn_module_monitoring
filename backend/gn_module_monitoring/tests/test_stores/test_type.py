import datetime
import uuid

import pytest
import sqlalchemy as sa
from marshmallow import ValidationError

from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.tools.stores.base import STORE_MAP
from gn_module_monitoring.tools.stores.type import (
    BooleanStore,
    DateStore,
    DateTimeStore,
    FloatStore,
    IntegerStore,
    StringStore,
    UUIDStore,
)
from gn_module_monitoring.tools.utils import schema_context


def make_store(store_cls, config, field_name="my_field", entity="site"):
    with schema_context(entity=ENTITY_MAP[entity], field_name=field_name):
        return store_cls(config)


class TestRegistry:
    @pytest.mark.parametrize(
        "key,store_cls",
        [
            ("string", StringStore),
            ("bool", BooleanStore),
            ("integer", IntegerStore),
            ("float", FloatStore),
            ("date", DateStore),
            ("datetime", DateTimeStore),
            ("uuid", UUIDStore),
        ],
    )
    def test_store_is_registered_by_key(self, key, store_cls):
        assert STORE_MAP[key] is store_cls


class TestGetStoreFromColumn:
    @pytest.mark.parametrize(
        "attr_name,store_cls",
        [
            ("base_site_name", StringStore),
            ("first_use_date", DateTimeStore),
            ("uuid_base_site", UUIDStore),
        ],
    )
    def test_column_store(self, attr_name, store_cls):
        from gn_module_monitoring.tools.stores.base import BaseStore

        attr = sa.inspect(TMonitoringSites).attrs[attr_name]
        assert BaseStore.get_store_from_attr(attr) is store_cls


class TestWireType:
    @pytest.mark.parametrize(
        "store_cls,expected",
        [
            (StringStore, str),
            (BooleanStore, bool),
            (IntegerStore, int),
            (FloatStore, float),
            (DateStore, str),
            (DateTimeStore, str),
            (UUIDStore, str),
        ],
    )
    def test_wire_type(self, store_cls, expected):
        assert make_store(store_cls, {}).get_wire_type() is expected


class TestTypeStores:
    def test_extra_date_is_kept_as_sent(self):
        field = make_store(DateStore, {}, field_name="my_extra").to_field()
        assert field.deserialize("2026-01-02") == "2026-01-02"

    def test_extra_uuid_is_kept_as_sent(self):
        value = str(uuid.uuid4())
        field = make_store(UUIDStore, {}, field_name="my_extra").to_field()
        assert field.deserialize(value) == value

    def test_native_date_is_decoded(self):
        field = make_store(DateStore, {}, field_name="visit_date_min", entity="visit").to_field()
        assert field.deserialize("2026-01-02") == datetime.date(2026, 1, 2)

    def test_native_uuid_is_decoded(self):
        value = uuid.uuid4()
        field = make_store(UUIDStore, {}, field_name="uuid_base_site").to_field()
        assert field.deserialize(str(value)) == value

    def test_integer_rejects_string(self):
        field = make_store(IntegerStore, {}, field_name="my_extra").to_field()
        assert field.deserialize(3) == 3
        with pytest.raises(ValidationError):
            field.deserialize("3")

    def test_float_accepts_int(self):
        field = make_store(FloatStore, {}, field_name="my_extra").to_field()
        assert field.deserialize(3) == 3.0

    def test_boolean_rejects_string(self):
        field = make_store(BooleanStore, {}, field_name="my_extra").to_field()
        assert field.deserialize(True) is True
        with pytest.raises(ValidationError):
            field.deserialize("maybe")
