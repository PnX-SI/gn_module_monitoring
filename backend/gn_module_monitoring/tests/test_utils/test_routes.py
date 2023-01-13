import pytest
from werkzeug.datastructures import MultiDict

from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import MonitoringSitesSchema
from gn_module_monitoring.utils.routes import get_limit_offset, paginate


@pytest.mark.parametrize("limit, offset", [("1", "2"), (1, 2), ("1", 2), (1, "2")])
def test_get_limit_offset(limit, offset):
    multi_dict = MultiDict([("limit", limit), ("offset", offset)])

    comp_limit, comp_offset = get_limit_offset(params=multi_dict)

    assert isinstance(comp_limit, int)
    assert isinstance(comp_offset, int)


def test_paginate(sites):
    limit = 1
    page = 2

    res = paginate(
        query=TMonitoringSites.query, schema=MonitoringSitesSchema, limit=limit, page=page
    )

    assert res.json["offset"] == page
