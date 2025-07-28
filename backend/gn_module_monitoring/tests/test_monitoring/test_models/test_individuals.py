import pytest

from geonature.core.gn_monitoring.models import TIndividuals
from gn_module_monitoring.monitoring.models import (
    PermissionModel,
    TMonitoringIndividuals,
    MonitoringQuery,
)
from gn_module_monitoring.tests.fixtures.individual import *
from gn_module_monitoring.tests.fixtures.observation import *


class TestMonitoringIndividuals:
    def test_model_inheritance(self):
        assert issubclass(TMonitoringIndividuals, TIndividuals)
        assert issubclass(TMonitoringIndividuals, PermissionModel)
        assert issubclass(TMonitoringIndividuals, MonitoringQuery)

    def test_nb_sites(
        self, individuals, sites, visit_with_individual, observation_with_individual
    ):
        assert individuals["individual_with_site"].nb_sites == 1
        assert individuals["orphan_individual"].nb_sites == 0
