import pytest
from geonature.tests.fixtures import *
from geonature.tests.fixtures import _session, app, _app, users
from geonature.tests.test_monitoring import markings, nomenclature_type_markings
from gn_module_monitoring.tests.fixtures import *
from pypnusershub.tests.fixtures import teardown_logout_user


@pytest.fixture(scope="session", autouse=True)
def _create_users_first(users):
    """Force la création de la fixture de session `users` avant toute transaction de
    classe/fonction : sinon, si le premier test d'une classe ne l'utilise pas, les
    utilisateurs sont créés dans le savepoint de la classe et supprimés à son rollback,
    ce qui casse les classes de tests suivantes."""
    return users
