import pytest

from gn_module_monitoring.config.entities.fields import EntityFieldConfigSchema


@pytest.mark.parametrize("expression", ['size("abc") > 2', "data.x == 1 && true", "true ? 1 : 2"])
def test_required_cel_accepts_valid_expression(expression):
    assert EntityFieldConfigSchema().validate({"required_cel": expression}) == {}


@pytest.mark.parametrize("expression", ["1 +", ""])
def test_required_cel_rejects_invalid_expression(expression):
    errors = EntityFieldConfigSchema().validate({"required_cel": expression})
    assert "required_cel" in errors


def test_required_cel_is_optional():
    assert EntityFieldConfigSchema().validate({}) == {}


@pytest.mark.parametrize("required", [True, False])
def test_required_and_required_cel_are_exclusive(required):
    errors = EntityFieldConfigSchema().validate({"required": required, "required_cel": "true"})
    assert "_schema" in errors


@pytest.mark.parametrize("expression", ["value > 10 && value < 20", "true"])
def test_validate_cel_accepts_valid_expression(expression):
    assert EntityFieldConfigSchema().validate({"validate_cel": expression}) == {}


def test_validate_cel_rejects_invalid_expression():
    errors = EntityFieldConfigSchema().validate({"validate_cel": "value > 10 and value < 20"})
    assert "validate_cel" in errors


def test_validate_cel_is_optional():
    assert EntityFieldConfigSchema().validate({}) == {}


def test_validate_cel_accepts_list_of_conditions_and_objects():
    value = ["value > 10", {"condition": "value < 20", "message": "Trop grand"}]
    assert EntityFieldConfigSchema().validate({"validate_cel": value}) == {}


def test_validate_cel_rejects_invalid_condition_in_list():
    errors = EntityFieldConfigSchema().validate({"validate_cel": ["value > 10 and value < 20"]})
    assert "validate_cel" in errors
