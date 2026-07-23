import datetime
import pytest

from geonature.utils.env import db
from sqlalchemy import select
from gn_module_monitoring.monitoring.models import TMonitoringModules

from gn_module_monitoring.monitoring.models import TMonitoringVisits


@pytest.fixture
def installed_module(install_module_test_with_config):
    return db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one_or_none()


@pytest.fixture
def visits(sites, datasets, installed_module):
    visit_date_min = datetime.datetime.strptime("2025-01-01", "%Y-%m-%d").date()
    dataset = datasets["orphan_dataset"]
    db_visits = []
    for site in sites.values():
        db_visits.append(
            TMonitoringVisits(
                id_base_site=site.id_base_site,
                id_module=installed_module.id_module,
                id_dataset=dataset.id_dataset,
                visit_date_min=visit_date_min,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_visits)
    db.session.flush()
    return db_visits


@pytest.fixture
def visit_with_individual(sites, datasets, users, monitoring_module):
    user = users["user"]
    now = datetime.datetime.now()
    dataset = datasets["orphan_dataset"]
    db_visit = TMonitoringVisits(
        id_base_site=sites["no-type"].id_base_site,
        id_module=monitoring_module.id_module,
        id_dataset=dataset.id_dataset,
        visit_date_min=now,
        id_digitiser=user.id_role,
    )
    with db.session.begin_nested():
        db.session.add(db_visit)
    return db_visit
