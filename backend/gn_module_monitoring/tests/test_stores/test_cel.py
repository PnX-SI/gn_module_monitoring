import datetime
import uuid
from types import SimpleNamespace

import pytest
from marshmallow import ValidationError

from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.modules.entities.base import (
    _CEL_SKIP,
    BaseEntity,
    CELMixin,
    get_app_timezone,
    to_cel_value,
)
from gn_module_monitoring.tools.stores.type import IntegerStore, StringStore
from gn_module_monitoring.tools.utils import normalize_cel_conditions, schema_context

M = "The following condition is not met: {}"


@pytest.fixture
def app_tz(monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Paris")
    get_app_timezone.cache_clear()
    yield
    get_app_timezone.cache_clear()


def make_store(store_cls, field_name, required_cel=None, validate_cel=None):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        return store_cls({}, required_cel=required_cel, validate_cel=validate_cel)


def build_schema(stores, validate_cel=None):
    site_cls = ENTITY_MAP["site"]
    entity_data = {"fields": {name: {"store": store} for name, store in stores.items()}}
    if validate_cel is not None:
        entity_data["validate_cel"] = normalize_cel_conditions(validate_cel)
    fake = SimpleNamespace(
        data=entity_data,
        model_schema_class=site_cls.model_schema_class,
    )
    fake._build_extra_data_schema = lambda extra: BaseEntity._build_extra_data_schema(fake, extra)
    return BaseEntity._build_extended_schema(fake, ())


def load_messages(schema, payload):
    try:
        schema().load(payload)
    except ValidationError as e:
        return e.messages
    return None


class TestToCelValue:
    @pytest.mark.parametrize("value", [None, True, 3, 1.5, "abc", b"ab"])
    def test_scalar_is_kept(self, value):
        assert to_cel_value(value) == value

    def test_uuid_becomes_string(self):
        value = uuid.UUID(int=1)
        assert to_cel_value(value) == str(value)

    def test_date_is_midnight_in_app_timezone(self, app_tz):
        value = to_cel_value(datetime.date(2026, 1, 2))
        assert value.ToJsonString() == "2026-01-01T23:00:00Z"

    def test_naive_datetime_is_in_app_timezone(self, app_tz):
        value = to_cel_value(datetime.datetime(2026, 1, 2, 10))
        assert value.ToJsonString() == "2026-01-02T09:00:00Z"

    def test_aware_datetime_keeps_its_timezone(self, app_tz):
        value = datetime.datetime(2026, 1, 2, 10, tzinfo=datetime.timezone.utc)
        assert to_cel_value(value).ToJsonString() == "2026-01-02T10:00:00Z"

    def test_list_converts_each_item(self):
        assert to_cel_value([1, None, "a"]) == [1, None, "a"]

    def test_list_with_unsupported_item_is_skipped(self):
        assert to_cel_value([1, object()]) is _CEL_SKIP

    def test_dict_converts_each_value(self):
        assert to_cel_value({"a": 1, "b": [1, 2]}) == {"a": 1, "b": [1, 2]}

    def test_dict_with_non_string_key_is_skipped(self):
        assert to_cel_value({1: "a"}) is _CEL_SKIP

    def test_dict_with_unsupported_value_is_skipped(self):
        assert to_cel_value({"a": object()}) is _CEL_SKIP

    def test_unsupported_object_is_skipped(self):
        assert to_cel_value(object()) is _CEL_SKIP


class TestCheckRequiredCel:
    def test_schema_uses_cel_mixin(self):
        schema = build_schema({"value": make_store(IntegerStore, "value")})
        assert issubclass(schema, CELMixin)

    def test_condition_on_field_itself_with_missing_value_is_an_error(self):
        # Sur une valeur absente, `value` vaut null : la comparaison n’est pas booléenne
        schema = build_schema(
            {"value": make_store(IntegerStore, "value", 'value > 10 && value < 20')}
        )
        messages = load_messages(schema, {"base_site_name": "x"})
        assert "value" in messages["data"]
        assert "non booléenne" in messages["data"]["value"][0]

    def test_null_condition_on_field_itself_makes_field_required(self):
        schema = build_schema({"value": make_store(IntegerStore, "value", "value == null")})
        messages = load_messages(schema, {"base_site_name": "x"})
        assert messages == {"data": {"value": ["Champ requis."]}}

    def test_condition_on_field_itself_is_skipped_when_value_is_present(self):
        schema = build_schema(
            {"value": make_store(IntegerStore, "value", 'value > 10 && value < 20')}
        )
        assert load_messages(schema, {"base_site_name": "x", "value": 15}) is None

    @pytest.mark.parametrize(
        "payload,required",
        [
            ({"kind": "A"}, True),
            ({"kind": "B"}, False),
            ({}, False),
        ],
    )
    def test_condition_on_other_extra_field(self, payload, required):
        schema = build_schema(
            {
                "kind": make_store(StringStore, "kind"),
                "value": make_store(IntegerStore, "value", 'kind == "A"'),
            }
        )
        messages = load_messages(schema, {"base_site_name": "x", **payload})
        assert (messages == {"data": {"value": ["Champ requis."]}}) is required
        assert (messages is None) is not required

    @pytest.mark.parametrize(
        "name,required",
        [("x", True), ("y", False)],
    )
    def test_condition_on_native_field(self, name, required):
        schema = build_schema(
            {"value": make_store(IntegerStore, "value", 'base_site_name == "x"')}
        )
        messages = load_messages(schema, {"base_site_name": name})
        assert (messages == {"data": {"value": ["Champ requis."]}}) is required
        assert (messages is None) is not required

    @pytest.mark.parametrize(
        "kind,name,required",
        [
            ("A", "x", True),
            ("A", "z", False),
            ("B", "x", False),
        ],
    )
    def test_complex_condition_mixing_native_and_extra_fields(self, kind, name, required):
        schema = build_schema(
            {
                "kind": make_store(StringStore, "kind"),
                "value": make_store(
                    IntegerStore, "value", 'kind == "A" && base_site_name != "z"'
                ),
            }
        )
        messages = load_messages(schema, {"base_site_name": name, "kind": kind})
        assert (messages == {"data": {"value": ["Champ requis."]}}) is required
        assert (messages is None) is not required

    @pytest.mark.parametrize(
        "date,required",
        [("2026-01-02", True), ("2025-01-02", False)],
    )
    def test_condition_on_native_date(self, app_tz, date, required):
        schema = build_schema(
            {
                "value": make_store(
                    IntegerStore,
                    "value",
                    'first_use_date > timestamp("2026-01-01T22:00:00Z")',
                )
            }
        )
        messages = load_messages(schema, {"base_site_name": "x", "first_use_date": date})
        assert (messages == {"data": {"value": ["Champ requis."]}}) is required
        assert (messages is None) is not required

    def test_native_field_error_is_reported_at_top_level(self):
        schema = build_schema(
            {
                "kind": make_store(StringStore, "kind"),
                "base_site_description": make_store(
                    StringStore, "base_site_description", 'kind == "A"'
                ),
            }
        )
        messages = load_messages(schema, {"base_site_name": "x", "kind": "A"})
        assert messages == {"base_site_description": ["Champ requis."]}

    def test_non_boolean_condition_is_an_error(self):
        schema = build_schema({"value": make_store(IntegerStore, "value", "kind")})
        messages = load_messages(schema, {"base_site_name": "x"})
        assert "non booléenne" in messages["data"]["value"][0]

    def test_unknown_field_in_condition_is_an_error(self):
        schema = build_schema({"value": make_store(IntegerStore, "value", 'missing == "x"')})
        messages = load_messages(schema, {"base_site_name": "x"})
        assert "non booléenne" in messages["data"]["value"][0]


class TestValidateCel:
    def test_value_in_range_is_valid(self):
        schema = build_schema(
            {"value": make_store(IntegerStore, "value", validate_cel="value > 10 && value < 20")}
        )
        assert load_messages(schema, {"base_site_name": "x", "value": 15}) is None

    @pytest.mark.parametrize("value", [10, 20, 5])
    def test_value_out_of_range_is_invalid(self, value):
        schema = build_schema(
            {"value": make_store(IntegerStore, "value", validate_cel="value > 10 && value < 20")}
        )
        messages = load_messages(schema, {"base_site_name": "x", "value": value})
        assert messages == {"data": {"value": [M.format("value > 10 && value < 20")]}}

    def test_absent_value_is_not_validated(self):
        schema = build_schema(
            {"value": make_store(IntegerStore, "value", validate_cel="value > 10 && value < 20")}
        )
        assert load_messages(schema, {"base_site_name": "x"}) is None

    def test_absent_value_is_required_and_not_validated(self):
        schema = build_schema(
            {
                "value": make_store(
                    IntegerStore,
                    "value",
                    required_cel="kind == \"A\"",
                    validate_cel="value > 10 && value < 20",
                ),
                "kind": make_store(StringStore, "kind"),
            }
        )
        messages = load_messages(schema, {"base_site_name": "x", "kind": "A"})
        assert messages == {"data": {"value": ["Champ requis."]}}

    def test_cross_field_condition(self):
        schema = build_schema(
            {
                "limit": make_store(IntegerStore, "limit"),
                "value": make_store(IntegerStore, "value", validate_cel="value <= limit"),
            }
        )
        assert load_messages(schema, {"base_site_name": "x", "limit": 5, "value": 5}) is None
        messages = load_messages(schema, {"base_site_name": "x", "limit": 5, "value": 6})
        assert messages == {"data": {"value": [M.format("value <= limit")]}}

    def test_condition_on_native_field(self):
        schema = build_schema(
            {
                "base_site_description": make_store(
                    StringStore, "base_site_description", validate_cel="size(base_site_description) > 3"
                )
            }
        )
        assert load_messages(schema, {"base_site_name": "x", "base_site_description": "long"}) is None
        messages = load_messages(schema, {"base_site_name": "x", "base_site_description": "no"})
        assert messages == {"base_site_description": [M.format("size(base_site_description) > 3")]}

    def test_non_boolean_condition_is_an_error(self):
        schema = build_schema({"value": make_store(IntegerStore, "value", validate_cel="value")})
        messages = load_messages(schema, {"base_site_name": "x", "value": 3})
        assert "non booléenne" in messages["data"]["value"][0]


class TestEntityValidateCel:
    def test_condition_on_several_fields_is_valid(self):
        schema = build_schema(
            {
                "min_value": make_store(IntegerStore, "min_value"),
                "max_value": make_store(IntegerStore, "max_value"),
            },
            validate_cel="min_value <= max_value",
        )
        payload = {"base_site_name": "x", "min_value": 1, "max_value": 2}
        assert load_messages(schema, payload) is None

    def test_condition_on_several_fields_is_invalid(self):
        schema = build_schema(
            {
                "min_value": make_store(IntegerStore, "min_value"),
                "max_value": make_store(IntegerStore, "max_value"),
            },
            validate_cel="min_value <= max_value",
        )
        payload = {"base_site_name": "x", "min_value": 3, "max_value": 2}
        messages = load_messages(schema, payload)
        assert messages == {"_schema": [M.format("min_value <= max_value")]}

    def test_condition_mixing_native_and_extra_fields(self):
        schema = build_schema(
            {"value": make_store(IntegerStore, "value")},
            validate_cel='base_site_name != "z" || value == null',
        )
        assert load_messages(schema, {"base_site_name": "x"}) is None
        messages = load_messages(schema, {"base_site_name": "z", "value": 1})
        assert messages == {"_schema": [M.format('base_site_name != "z" || value == null')]}

    def test_condition_is_evaluated_even_without_fields(self):
        schema = build_schema({}, validate_cel="base_site_name == \"x\"")
        assert load_messages(schema, {"base_site_name": "x"}) is None
        messages = load_messages(schema, {"base_site_name": "y"})
        assert messages == {"_schema": [M.format('base_site_name == "x"')]}

    def test_non_boolean_condition_is_an_error(self):
        schema = build_schema({}, validate_cel="base_site_name")
        messages = load_messages(schema, {"base_site_name": "x"})
        assert "non booléenne" in messages["_schema"][0]

    def test_no_condition_means_no_error(self):
        schema = build_schema({"value": make_store(IntegerStore, "value")})
        assert load_messages(schema, {"base_site_name": "x", "value": 1}) is None


class TestValidateCelConditions:
    def test_string_gets_default_message(self):
        schema = build_schema({"value": make_store(IntegerStore, "value", validate_cel="value > 10")})
        messages = load_messages(schema, {"base_site_name": "x", "value": 5})
        assert messages == {"data": {"value": ["The following condition is not met: value > 10"]}}

    def test_object_message_is_used(self):
        conditions = [{"condition": "value > 10", "message": "Trop petit"}]
        schema = build_schema({"value": make_store(IntegerStore, "value", validate_cel=conditions)})
        messages = load_messages(schema, {"base_site_name": "x", "value": 5})
        assert messages == {"data": {"value": ["Trop petit"]}}

    def test_object_without_message_gets_default_message(self):
        conditions = [{"condition": "value > 10"}]
        schema = build_schema({"value": make_store(IntegerStore, "value", validate_cel=conditions)})
        messages = load_messages(schema, {"base_site_name": "x", "value": 5})
        assert messages == {"data": {"value": ["The following condition is not met: value > 10"]}}

    def test_every_failing_condition_reports_its_message(self):
        conditions = ["value > 10", {"condition": "value < 20", "message": "Trop grand"}, "value != 15"]
        schema = build_schema({"value": make_store(IntegerStore, "value", validate_cel=conditions)})
        messages = load_messages(schema, {"base_site_name": "x", "value": 15})
        assert messages == {"data": {"value": ["The following condition is not met: value != 15"]}}
        messages = load_messages(schema, {"base_site_name": "x", "value": 25})
        assert messages == {"data": {"value": ["Trop grand"]}}

    def test_entity_level_list_with_messages(self):
        conditions = [
            {"condition": "min_value <= max_value", "message": "min > max"},
            "min_value >= 0",
        ]
        schema = build_schema(
            {
                "min_value": make_store(IntegerStore, "min_value"),
                "max_value": make_store(IntegerStore, "max_value"),
            },
            validate_cel=conditions,
        )
        messages = load_messages(schema, {"base_site_name": "x", "min_value": 3, "max_value": 2})
        assert messages == {"_schema": ["min > max"]}

    @pytest.mark.parametrize(
        "value",
        [
            42,
            [42],
            {"message": "no condition"},
            {"condition": 42},
            {"condition": "value > 10", "unknown": True},
            {"condition": "value > 10", "message": 42},
            ["value > 10 and value < 20"],
        ],
    )
    def test_invalid_values_are_rejected(self, value):
        with pytest.raises(ValidationError):
            make_store(IntegerStore, "value", validate_cel=value)
