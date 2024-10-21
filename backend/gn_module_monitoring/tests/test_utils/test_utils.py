import pytest
from gn_module_monitoring.utils.utils import to_int


def test_to_int_valid():
    assert to_int("3") == 3


def test_to_int_invalid():
    assert to_int("hello") == None
