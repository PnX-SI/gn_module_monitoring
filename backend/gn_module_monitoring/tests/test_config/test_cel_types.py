import pytest
from marshmallow import ValidationError

from cel_expr_python.cel import Type

from gn_module_monitoring.config.entities.base import CEL_TYPES_MAP, check_cel_types
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.stores.type import (
    BooleanStore,
    DateStore,
    DateTimeStore,
    FloatStore,
    IntegerStore,
    StringStore,
    UUIDStore,
)
from gn_module_monitoring.tools.utils import normalize_cel_conditions, schema_context


def make_field(store_cls, field_name, required_cel=None, validate_cel=None, hidden_cel=None):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        store = store_cls({}, required_cel=required_cel, validate_cel=validate_cel)
    return {"store": store, "widget": {"hidden_cel": hidden_cel} if hidden_cel else {}}


FIELDS = {
    "number": make_field(IntegerStore, "number"),
    "ratio": make_field(FloatStore, "ratio"),
    "label": make_field(StringStore, "label"),
    "flag": make_field(BooleanStore, "flag"),
    "date": make_field(DateStore, "date"),
}


def errors_for(expression, key="required_cel", fields=FIELDS):
    fields = {name: dict(field) for name, field in fields.items()}
    fields["target"] = make_field(StringStore, "target", **{key: expression})
    try:
        check_cel_types(fields, None)
    except ValidationError as e:
        return e.messages
    return None


@pytest.mark.parametrize(
    "expression",
    [
        "fields.number == 1",
        "fields.number == null || fields.number > 3",
        "fields.label == 'Oui' && fields.flag",
        "fields.ratio > 1.5",
        "fields.date < timestamp('2026-01-01T00:00:00Z')",
        "fields.date == null",
    ],
)
def test_well_typed_boolean_expression_is_valid(expression):
    assert errors_for(expression) is None


@pytest.mark.parametrize(
    "expression",
    [
        "fields.number == 'a'",
        "fields.label > 3",
        "fields.number + 'x' == 1",
        "fields.date < 3",
    ],
)
def test_type_mismatch_is_an_error(expression):
    messages = errors_for(expression)
    assert messages is not None
    assert "target" in messages["fields"]
    assert "required_cel" in messages["fields"]["target"]


def test_non_boolean_expression_is_an_error():
    messages = errors_for("fields.number")
    assert "non booléenne" in messages["fields"]["target"]["required_cel"][0]


def test_unknown_field_is_an_error():
    messages = errors_for("fields.missing == 1")
    assert "missing" in messages["fields"]["target"]["required_cel"][0]


def test_validate_cel_is_typed_per_condition():
    fields = {name: dict(field) for name, field in FIELDS.items()}
    fields["target"] = make_field(
        StringStore,
        "target",
        validate_cel=normalize_cel_conditions(["fields.number > 3", "fields.number == 'a'"]),
    )
    with pytest.raises(ValidationError) as e:
        check_cel_types(fields, None)
    assert len(e.value.messages["fields"]["target"]["validate_cel"]) == 1


def test_hidden_cel_is_typed():
    messages = errors_for("fields.number == 1", key="hidden_cel")
    assert messages is None
    fields = {name: dict(field) for name, field in FIELDS.items()}
    fields["target"] = make_field(StringStore, "target", hidden_cel="fields.label > 3")
    with pytest.raises(ValidationError) as e:
        check_cel_types(fields, None)
    assert "hidden_cel" in e.value.messages["fields"]["target"]


def test_entity_validate_cel_is_typed():
    conditions = normalize_cel_conditions(["fields.number > 3", "fields.label == 1"])
    with pytest.raises(ValidationError) as e:
        check_cel_types(FIELDS, conditions)
    assert len(e.value.messages["validate_cel"]) == 1


@pytest.mark.parametrize("expression", ["fields.number +", ""])
def test_syntax_error_is_an_error(expression):
    messages = errors_for(expression)
    assert "invalide" in messages["fields"]["target"]["required_cel"][0]


@pytest.mark.parametrize(
    "store_cls, expected",
    [
        (IntegerStore, "google.protobuf.Int64Value"),
        (FloatStore, "google.protobuf.DoubleValue"),
        (BooleanStore, "google.protobuf.BoolValue"),
        (StringStore, "google.protobuf.StringValue"),
        (UUIDStore, "google.protobuf.StringValue"),
        (DateStore, "google.protobuf.Timestamp"),
        (DateTimeStore, "google.protobuf.Timestamp"),
    ],
)
def test_cel_types_map_uses_python_type(store_cls, expected):
    store = make_field(store_cls, "value")["store"]
    assert CEL_TYPES_MAP.get(store.get_python_type(), Type.DYN) == Type(expected)
