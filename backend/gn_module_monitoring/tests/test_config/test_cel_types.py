import pytest
from marshmallow import ValidationError

from cel_expr_python.cel import Type

from gn_module_monitoring.config.entities.base import (
    CEL_TYPES_MAP,
    cel_variable_type,
    compile_entity_cel_expressions,
)
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
from gn_module_monitoring.tools.utils import CELValidationsField, schema_context


def make_field(
    store_cls, field_name, required=False, required_cel=None, validate_cel=None, hidden_cel=None
):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        store = store_cls(
            {}, required=required, required_cel=required_cel, validate_cel=validate_cel
        )
    return {"store": store, "widget": {"hidden_cel": hidden_cel} if hidden_cel else {}}


# Champs requis : variables typées
# Fonctions (et non constantes de module) : `make_field` nécessite un contexte d'application Flask,
# absent au moment de la collecte pytest.
def typed_fields():
    return {
        "number": make_field(IntegerStore, "number", required=True),
        "ratio": make_field(FloatStore, "ratio", required=True),
        "label": make_field(StringStore, "label", required=True),
        "flag": make_field(BooleanStore, "flag", required=True),
        "date": make_field(DateStore, "date", required=True),
    }


# Champs optionnels : variables DYN, pouvant être vides
def nullable_fields():
    return {
        "number": make_field(IntegerStore, "number"),
        "label": make_field(StringStore, "label"),
        "date": make_field(DateStore, "date"),
    }


def errors_for(expression, key="required_cel", fields=None):
    if fields is None:
        fields = typed_fields()
    fields = {name: dict(field) for name, field in fields.items()}
    fields["target"] = make_field(StringStore, "target", **{key: expression})
    try:
        compile_entity_cel_expressions({"fields": fields})
    except ValidationError as e:
        return e.messages
    return None


@pytest.mark.parametrize(
    "expression",
    [
        "fields.number == 1",
        "fields.label == 'Oui' && fields.flag",
        "fields.ratio > 1.5",
        "fields.date < timestamp('2026-01-01T00:00:00Z')",
    ],
)
def test_well_typed_expression_is_valid(expression):
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
def test_type_mismatch_on_required_field_is_an_error(expression):
    messages = errors_for(expression)
    assert messages is not None
    assert "target" in messages["fields"]
    assert "required_cel" in messages["fields"]["target"]


@pytest.mark.parametrize(
    "expression",
    [
        "fields.number == null || fields.number > 3",
        "fields.date == null",
    ],
)
def test_null_comparison_on_optional_field_is_valid(expression):
    assert errors_for(expression, fields=nullable_fields()) is None


def test_optional_field_is_not_type_checked():
    assert errors_for("fields.number == 'a'", fields=nullable_fields()) is None


def test_non_boolean_expression_is_an_error():
    messages = errors_for("fields.number")
    assert "non booléenne" in messages["fields"]["target"]["required_cel"][0]


def test_unknown_field_is_an_error():
    messages = errors_for("fields.missing == 1")
    assert "missing" in messages["fields"]["target"]["required_cel"][0]


def test_validate_cel_is_typed_per_condition():
    fields = {name: dict(field) for name, field in typed_fields().items()}
    fields["target"] = make_field(
        StringStore,
        "target",
        validate_cel=CELValidationsField().deserialize(
            ["fields.number > 3", "fields.number == 'a'"]
        ),
    )
    with pytest.raises(ValidationError) as e:
        compile_entity_cel_expressions({"fields": fields})
    assert len(e.value.messages["fields"]["target"]["validate_cel"]) == 1


def test_hidden_cel_is_typed():
    messages = errors_for("fields.number == 1", key="hidden_cel")
    assert messages is None
    fields = {name: dict(field) for name, field in typed_fields().items()}
    fields["target"] = make_field(StringStore, "target", hidden_cel="fields.label > 3")
    with pytest.raises(ValidationError) as e:
        compile_entity_cel_expressions({"fields": fields})
    assert "hidden_cel" in e.value.messages["fields"]["target"]


def test_entity_validate_cel_is_typed():
    conditions = CELValidationsField().deserialize(["fields.number > 3", "fields.label == 1"])
    with pytest.raises(ValidationError) as e:
        compile_entity_cel_expressions({"fields": typed_fields(), "validate_cel": conditions})
    assert len(e.value.messages["validate_cel"]) == 1


@pytest.mark.parametrize("expression", ["fields.number +", ""])
def test_syntax_error_is_an_error(expression):
    messages = errors_for(expression)
    assert "invalide" in messages["fields"]["target"]["required_cel"][0]


def test_compiled_expressions_are_stored_by_field():
    fields = {name: dict(field) for name, field in typed_fields().items()}
    fields["target"] = make_field(
        StringStore,
        "target",
        required_cel="fields.number > 1",
        validate_cel=CELValidationsField().deserialize(["fields.number < 10"]),
    )
    data = compile_entity_cel_expressions(
        {
            "fields": fields,
            "validate_cel": CELValidationsField().deserialize(["fields.number != 5"]),
        }
    )
    assert fields["target"]["compiled_required_cel"] is not None
    assert [message for _, message in fields["target"]["compiled_validate_cel"]] == [
        "The following condition is not met: fields.number < 10"
    ]
    assert fields["number"]["compiled_required_cel"] is None
    assert fields["number"]["compiled_validate_cel"] == []
    assert len(data["compiled_validate_cel"]) == 1


@pytest.mark.parametrize(
    "store_cls, expected",
    [
        (IntegerStore, Type.INT),
        (FloatStore, Type.DOUBLE),
        (BooleanStore, Type.BOOL),
        (StringStore, Type.STRING),
        (UUIDStore, Type.STRING),
        (DateStore, Type("google.protobuf.Timestamp")),
        (DateTimeStore, Type("google.protobuf.Timestamp")),
    ],
)
def test_required_scalar_has_a_cel_type(store_cls, expected):
    store = make_field(store_cls, "value", required=True)["store"]
    assert cel_variable_type(store) == expected
    assert CEL_TYPES_MAP[store.get_python_type()] == expected


@pytest.mark.parametrize("store_cls", [IntegerStore, StringStore, DateStore])
def test_optional_field_is_dyn(store_cls):
    store = make_field(store_cls, "value")["store"]
    assert cel_variable_type(store) == Type.DYN
