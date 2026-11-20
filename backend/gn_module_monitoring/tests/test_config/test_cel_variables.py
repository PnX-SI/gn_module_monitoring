from types import SimpleNamespace

import pytest

from cel_expr_python.cel import NewEnv, Type

from gn_module_monitoring.config.entities.base import compile_entity_cel_expressions
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.stores.type import IntegerStore, StringStore
from gn_module_monitoring.tools.utils import (
    CELValidationsField,
    cel_entity_variables,
    cel_used_variables,
    compile_cel_expression,
    schema_context,
)

ENV = NewEnv(
    variables={
        "fields.a": Type.DYN,
        "fields.b": Type.INT,
        "fields.c": Type.DYN,
        "fields.d": Type.STRING,
    }
)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("fields.a.cd_nomenclature == 'x'", {"fields.a"}),
        ("fields.a.b.c == 1 && fields.b > 2", {"fields.a", "fields.b"}),
        ("fields.a == null || fields.c > 3", {"fields.a", "fields.c"}),
        ("size(fields.d) > 3", {"fields.d"}),
        ("fields.b > 2 ? fields.c : false", {"fields.b", "fields.c"}),
        ("1 == 1", set()),
    ],
)
def test_used_variables_of_expression(expression, expected):
    compiled = compile_cel_expression(ENV, expression)
    assert cel_used_variables(compiled) == expected


def make_entity(fields, validate_cel=None):
    data = {"fields": fields, "validate_cel": validate_cel}
    compile_entity_cel_expressions(data)
    return SimpleNamespace(data=data)


def make_field(store_cls, field_name, required_cel=None, validate_cel=None, hidden_cel=None):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        store = store_cls(
            {},
            required_cel=required_cel,
            validate_cel=CELValidationsField().deserialize(validate_cel) if validate_cel else None,
        )
    return {"store": store, "widget": {"hidden_cel": hidden_cel} if hidden_cel else {}}


def test_entity_variables_collects_all_expressions():
    entity = make_entity(
        {
            "kind": make_field(StringStore, "kind"),
            "value": make_field(
                IntegerStore,
                "value",
                required_cel='fields.kind == "A"',
                validate_cel=["fields.value > fields.limit"],
            ),
            "limit": make_field(IntegerStore, "limit", hidden_cel="fields.kind == 'B'"),
            "other": make_field(IntegerStore, "other"),
        },
        validate_cel=CELValidationsField().deserialize(["fields.value != fields.other"]),
    )
    assert cel_entity_variables(entity) == [
        "fields.kind",
        "fields.limit",
        "fields.other",
        "fields.value",
    ]


def test_entity_without_expressions_has_no_variables():
    entity = make_entity({"kind": make_field(StringStore, "kind")})
    assert cel_entity_variables(entity) == []
