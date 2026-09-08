import pytest
from werkzeug.datastructures import MultiDict

from sqlalchemy import select

from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import MonitoringSitesSchema
from gn_module_monitoring.utils.routes import get_limit_page, paginate


@pytest.mark.parametrize("limit, page", [("1", "2"), (1, 2), ("1", 2), (1, "2")])
def test_get_limit_page(limit, page):
    multi_dict = MultiDict([("limit", limit), ("page", page)])

    comp_limit, comp_page = get_limit_page(params=multi_dict)

    assert isinstance(comp_limit, int)
    assert isinstance(comp_page, int)


def test_paginate(sites):
    limit = 1
    page = 2

    res = paginate(
        query=select(TMonitoringSites), schema=MonitoringSitesSchema, limit=limit, page=page
    )

    assert res.json["page"] == page


def test_paginate_args(sites):
    limit = 1
    page = 1
    schema_extra_args = {"exclude": ("items.medias", "items.parents")}
    res = paginate(
        query=select(TMonitoringSites),
        schema=MonitoringSitesSchema,
        limit=limit,
        page=page,
        schema_extra_args=schema_extra_args,
    )

    items_keys = set(res.json["items"][0].keys())
    assert set(("medias", "parents")).isdisjoint(items_keys)
