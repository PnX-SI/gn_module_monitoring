import datetime

import pytest
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringVisits


@pytest.fixture
def visits(module, users, types_site, sites, datasets):
    now = datetime.datetime.now()
    dataset = datasets["orphan_dataset"]
    db_visits = []
    for site in sites.values():
        db_visits.append(
            TMonitoringVisits(
                id_base_site=site.id_base_site,
                id_module=module.id_module,
                id_dataset=dataset.id_dataset,
                visit_date_min=now,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_visits)

    return db_visits
