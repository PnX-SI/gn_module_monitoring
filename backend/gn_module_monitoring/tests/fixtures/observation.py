import pytest

from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringObservations


@pytest.fixture
def observation_with_individual(visit_with_individual, individuals, monitoring_module):
    db_observation = TMonitoringObservations(
        id_base_visit=visit_with_individual.id_base_visit,
        cd_nom=individuals["individual_with_site"].cd_nom,
        id_digitiser=visit_with_individual.id_digitiser,
        id_individual=individuals["individual_with_site"].id_individual,
    )
    with db.session.begin_nested():
        db.session.add(db_observation)
    return db_observation
