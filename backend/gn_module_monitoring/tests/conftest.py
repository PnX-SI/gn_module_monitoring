import pytest
from flask import current_app
from geonature.tests.fixtures import *
from geonature.tests.fixtures import _session, app, _app, users
from geonature.tests.test_monitoring import markings, nomenclature_type_markings
from gn_module_monitoring.tests.fixtures import *
from pypnusershub.tests.fixtures import teardown_logout_user

from gn_module_monitoring import EXTENSION_CODE
from gn_module_monitoring.tools.stores.relationships.utils import (
    get_nomenclature,
    get_nomenclature_type,
)


@pytest.fixture(autouse=True)
def _clear_monitoring_caches(app):
    """Les modules monitoring (`get_module`) et les nomenclatures (`@cache`) sont mis en cache
    au niveau de l'application : ils retiennent des instances ORM liées à la transaction du test
    précédent. Après son rollback, ces instances sont périmées (`ObjectDeletedError`).
    On vide donc les caches avant et après chaque test."""

    def clear():
        current_app.extensions[EXTENSION_CODE]["modules"].clear()
        get_nomenclature_type.cache_clear()
        get_nomenclature.cache_clear()

    clear()
    yield
    clear()


@pytest.fixture(scope="session", autouse=True)
def _create_users_first(users):
    """Force la création de la fixture de session `users` avant toute transaction de
    classe/fonction : sinon, si le premier test d'une classe ne l'utilise pas, les
    utilisateurs sont créés dans le savepoint de la classe et supprimés à son rollback,
    ce qui casse les classes de tests suivantes."""
    return users
