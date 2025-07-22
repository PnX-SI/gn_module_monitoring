import datetime
import pytest

from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringVisits


@pytest.fixture
def visits(sites, datasets, monitoring_module):
    now = datetime.datetime.now()
    dataset = datasets["orphan_dataset"]
    db_visits = []
    for site in sites.values():
        db_visits.append(
            TMonitoringVisits(
                id_base_site=site.id_base_site,
                id_module=monitoring_module.id_module,
                id_dataset=dataset.id_dataset,
                visit_date_min=now,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_visits)

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
