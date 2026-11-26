import gc
from contextlib import contextmanager

import pytest
import sqlalchemy as sa
from ref_geo.models import LAreas
from sqlalchemy import event

from geonature.utils.env import db
from gn_module_monitoring.tools.stores.relationships.cache import (
    CACHE_CONTEXT_KEY,
    RelationshipCache,
    get_instance,
)
from gn_module_monitoring.tools.utils import schema_context

MISSING_PK = 999_999_999


@pytest.fixture
def sql_counter():
    counter = {"n": 0}

    def count(conn, cursor, statement, params, context, executemany):
        counter["n"] += 1

    event.listen(db.engine, "before_cursor_execute", count)
    try:
        yield counter
    finally:
        event.remove(db.engine, "before_cursor_execute", count)


@contextmanager
def active_cache():
    cache = RelationshipCache()
    with schema_context(**{CACHE_CONTEXT_KEY: cache}):
        yield cache


@pytest.fixture
def area_ids():
    # Ne jamais détacher la session (fixtures de portée session) : on lit seulement les identifiants
    ids = db.session.scalars(sa.select(LAreas.id_area).order_by(LAreas.id_area).limit(3)).all()
    assert len(ids) == 3
    return ids


def _not_in_identity_map(ids):
    # Clé dont l'instance n'est pas déjà chargée dans la session : une lecture ira en base
    loaded = {o.id_area for o in db.session.identity_map.values() if isinstance(o, LAreas)}
    return next(i for i in ids if i not in loaded)


def test_sans_cache_get_instance_comme_session_get(area_ids):
    present, *_ = area_ids
    assert get_instance(LAreas, present) is db.session.get(LAreas, present)
    assert get_instance(LAreas, MISSING_PK) is None


def test_sans_cache_fallback_explicite(area_ids):
    sentinel = object()
    assert get_instance(LAreas, area_ids[0], lambda: sentinel) is sentinel


def test_cache_actif_cle_presente_sans_requete(area_ids, sql_counter):
    present, *_ = area_ids
    with active_cache() as cache:
        cache.prefetch(LAreas, area_ids)
        sql_counter["n"] = 0
        instance = get_instance(LAreas, present)
        assert instance is not None
        assert instance.id_area == present
        assert sql_counter["n"] == 0


def test_cache_actif_cle_prechargee_absente_sans_requete(area_ids, sql_counter):
    with active_cache() as cache:
        cache.prefetch(LAreas, [area_ids[0], MISSING_PK])
        sql_counter["n"] = 0
        assert get_instance(LAreas, MISSING_PK) is None
        assert sql_counter["n"] == 0


def test_cache_actif_cle_non_prechargee_repli(area_ids, sql_counter):
    fallback_id = _not_in_identity_map(area_ids)
    with active_cache() as cache:
        cache.prefetch(LAreas, [i for i in area_ids if i != fallback_id])
        sql_counter["n"] = 0
        instance = get_instance(LAreas, fallback_id)
        assert instance is not None
        assert instance.id_area == fallback_id
        assert sql_counter["n"] >= 1


def test_cache_actif_fallback_explicite_pour_cle_non_chargee(area_ids):
    sentinel = object()
    with active_cache() as cache:
        cache.prefetch(LAreas, [area_ids[0]])
        assert get_instance(LAreas, area_ids[1], lambda: sentinel) is sentinel


def test_prefetch_une_requete_par_modele(area_ids, sql_counter):
    with active_cache() as cache:
        sql_counter["n"] = 0
        cache.prefetch(LAreas, area_ids)
        assert sql_counter["n"] == 1
        cache.prefetch(LAreas, area_ids)
        assert sql_counter["n"] == 1


def test_sortie_du_contexte_desactive_le_cache(area_ids, sql_counter):
    fallback_id = _not_in_identity_map(area_ids)
    with active_cache() as cache:
        cache.prefetch(LAreas, [fallback_id])
        assert cache.get(LAreas, fallback_id, lambda: pytest.fail("non chargé")) is not None
    # Les références fortes disparaissent avec le cache : l'identity map libère les instances
    del cache
    gc.collect()
    sql_counter["n"] = 0
    assert get_instance(LAreas, fallback_id) is not None
    assert sql_counter["n"] >= 1
