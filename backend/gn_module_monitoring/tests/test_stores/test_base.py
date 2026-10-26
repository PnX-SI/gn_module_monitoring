from typing import Literal, Never

import pytest
import sqlalchemy as sa
from marshmallow import ValidationError

from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.tools.stores.base import (
    STORE_MAP,
    BaseStore,
    DummyStore,
    ListStore,
    ValueStore,
)
from gn_module_monitoring.tools.stores.relationships.m2m import TypesSiteStore
from gn_module_monitoring.tools.stores.relationships.m2o import SitesGroupStore, UserStore
from gn_module_monitoring.tools.stores.type import StringStore
from gn_module_monitoring.tools.utils import schema_context


def make_store(store_cls, config, field_name="my_field", entity="site", **kwargs):
    with schema_context(entity=ENTITY_MAP[entity], field_name=field_name):
        return store_cls(config, **kwargs)


class TestRegistry:
    @pytest.mark.parametrize(
        "key,store_cls",
        [
            ("dummy", DummyStore),
            ("value", ValueStore),
            ("list", ListStore),
            ("user", UserStore),
            ("sites_group", SitesGroupStore),
            ("types_site", TypesSiteStore),
        ],
    )
    def test_store_is_registered_by_key(self, key, store_cls):
        assert STORE_MAP[key] is store_cls

    def test_class_without_key_is_not_registered(self):
        class AnonymousStore(BaseStore):
            pass

        assert AnonymousStore not in STORE_MAP.values()


class TestConfigSchema:
    def test_default_type_comes_from_store_class(self):
        store = make_store(StringStore, {})
        assert store["type"] == "string"
        assert store.required is False
        assert store.required_cel is None

    def test_unknown_key_is_rejected(self):
        with pytest.raises(ValidationError):
            make_store(StringStore, {"type": "string", "unknown_option": True})


class TestGetStoreFromAttr:
    @pytest.mark.parametrize(
        "attr_name,store_cls",
        [
            ("id_inventor", UserStore),
            ("id_sites_group", SitesGroupStore),
        ],
    )
    def test_foreign_key_store(self, attr_name, store_cls):
        attr = sa.inspect(TMonitoringSites).attrs[attr_name]
        assert BaseStore.get_store_from_attr(attr) is store_cls

    def test_relationship_store(self):
        attr = sa.inspect(TMonitoringSites).relationships["types_site"]
        assert BaseStore.get_store_from_attr(attr) is TypesSiteStore

    def test_unknown_attr_raises(self):
        class FakeAttr:
            key = "fake"

        with pytest.raises(ValueError):
            BaseStore.get_store_from_attr(FakeAttr())


class TestBaseStore:
    def test_store_keeps_entity_and_field_name(self):
        store = make_store(StringStore, {}, field_name="base_site_name")
        assert store.entity is ENTITY_MAP["site"]
        assert store.field_name == "base_site_name"
        assert store.native_attr is not None

    def test_extra_field_has_no_native_attr(self):
        store = make_store(StringStore, {}, field_name="my_extra")
        assert store.native_attr is None

    def test_dummy_store_has_no_wire_type(self):
        assert make_store(DummyStore, {}).get_wire_type() is Never


class TestRequired:
    def test_required_field_rejects_none(self):
        field = make_store(StringStore, {}, required=True).to_field()
        assert field.required is True
        with pytest.raises(ValidationError):
            field.deserialize(None)

    def test_optional_field_accepts_none(self):
        field = make_store(StringStore, {}).to_field()
        assert field.required is False
        assert field.deserialize(None) is None


class TestValueStore:
    VALUES = [{"value": "a", "label": "A"}, "b"]

    def test_accepts_allowed_value(self):
        field = make_store(ValueStore, {"values": self.VALUES}).to_field()
        assert field.deserialize("a") == "a"
        assert field.deserialize("b") == "b"

    def test_rejects_other_value(self):
        field = make_store(ValueStore, {"values": self.VALUES}).to_field()
        with pytest.raises(ValidationError):
            field.deserialize("c")

    def test_wire_type_is_literal_of_values(self):
        store = make_store(ValueStore, {"values": self.VALUES})
        assert store.get_wire_type() == Literal["a", "b"]


class TestListStore:
    VALUES = [{"value": "a", "label": "A"}, "b"]

    def test_accepts_list_of_allowed_values(self):
        field = make_store(ListStore, {"values": self.VALUES}).to_field()
        assert field.deserialize(["a", "b"]) == ["a", "b"]

    def test_rejects_list_with_other_value(self):
        field = make_store(ListStore, {"values": self.VALUES}).to_field()
        with pytest.raises(ValidationError):
            field.deserialize(["a", "c"])

    def test_wire_type_is_list_of_literal(self):
        store = make_store(ListStore, {"values": self.VALUES})
        assert store.get_wire_type() == list[Literal["a", "b"]]
