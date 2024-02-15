import pytest
from gn_module_monitoring.utils.errors.errorHandler import InvalidUsage


def test_invalid_usage():
    with pytest.raises(InvalidUsage) as error:
        raise InvalidUsage("this is an invalid usage")
    assert error.type == InvalidUsage
    assert (
        str(error.value)
        == "Error 400, Message: this is an invalid usage, raised error: InvalidUsage"
    )
    assert error.value.to_dict() == (
        {
            "message": "this is an invalid usage",
            "payload": None,
            "status_code": 400,
        },
        400,
    )
