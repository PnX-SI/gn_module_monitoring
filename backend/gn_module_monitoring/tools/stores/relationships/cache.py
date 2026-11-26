"""
Cache permettant de pré-charger des objets liés (instances de modèles) pour les stores de relation.

Un `RelationshipCache` est actif lorsqu'il est placé dans `schema_context` sous la clé
`CACHE_CONTEXT_KEY` ; il cesse de l'être en sortie du contexte. Quand aucun cache n'est actif, les
lectures passent directement par la base (`db.session.get`) : il n'existe aucun cache global.

- `RelationshipCache.prefetch(model, pks)` charge les instances par une requête `WHERE pk IN (...)`.
  Toutes les clés demandées sont enregistrées, y compris celles absentes en base (valeur `None`).
- `get_instance(model, pk)` lit le cache s'il est présent dans le `schema_context` et que `pk` y
  est enregistrée (instance, ou `None` si absente en base), sinon appelle `fallback` (par défaut
  `db.session.get`).
"""

from collections.abc import Callable, Iterable

import sqlalchemy as sa

from geonature.utils.env import db

from gn_module_monitoring.tools.utils import schema_context

CACHE_CONTEXT_KEY = "relationship_cache"


def _pk_loader(model):
    # Seules les clés primaires simples (une colonne) sont supportées : la clé composite n'est pas gérée.
    mapper = sa.inspect(model)
    attr_name = mapper.get_property_by_column(mapper.primary_key[0]).key

    def load(pks):
        instances = db.session.scalars(
            sa.select(model).where(getattr(model, attr_name).in_(pks))
        ).all()
        return {getattr(instance, attr_name): instance for instance in instances}

    return load


class RelationshipCache:
    """Instances pré-chargées, par modèle puis par clé primaire (`None` si absente en base)."""

    def __init__(self):
        self._objects: dict[type, dict] = {}

    def prefetch(self, model: type, pks: Iterable) -> None:
        """Charge en une requête les instances `model` de clés primaires `pks` non encore connues."""
        objects = self._objects.setdefault(model, {})
        pending = [pk for pk in dict.fromkeys(pks) if pk is not None and pk not in objects]
        if pending:
            found = _pk_loader(model)(pending)
            objects.update({pk: found.get(pk) for pk in pending})

    def get(self, model: type, pk, fallback: Callable):
        """
        Instance `model` de clé primaire `pk` si elle a été enregistrée par `prefetch`
        (`None` si absente en base), sinon `fallback()`.
        """
        objects = self._objects.get(model, {})
        if pk in objects:
            return objects[pk]
        return fallback()


def get_instance(model, pk, fallback: Callable | None = None):
    """
    Instance `model` de clé primaire `pk`, ou `None` si absente.
    Lit le cache s'il est présent dans le `schema_context` et que `pk` y est enregistrée (sans
    requête) ; sinon appelle `fallback()` (par défaut `db.session.get(model, pk)`).
    """
    if fallback is None:
        fallback = lambda: db.session.get(model, pk)
    context = schema_context.get()
    cache = context.get(CACHE_CONTEXT_KEY) if context else None
    if cache is None:
        return fallback()
    return cache.get(model, pk, fallback)
