import pytest
from werkzeug.datastructures import MultiDict
from flask import g

from sqlalchemy import select
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringSites, TMonitoringModules
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

    # Reload the module from the database. If not it can trigger ObjectDeletedError
    monitoring_module = db.session.scalar(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    )
    g.current_module = monitoring_module

    res = paginate(
        query=select(TMonitoringSites), schema=MonitoringSitesSchema, limit=limit, page=page
    )

    assert res.json["page"] == page
