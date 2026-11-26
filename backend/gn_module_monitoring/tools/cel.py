"""
Conversion des valeurs chargées en valeurs CEL (`fields.<nom>` des expressions).

- `value_to_cel` : valeurs Python (scalaires, dates, uuid, listes, dicts) ;
- `object_to_cel` : instance de modèle (objet chargé par une relation), convertie en dict de ses colonnes.

Ce sont les stores qui décident de la conversion (`BaseStore.to_cel`) : le schéma ne dispatche pas sur le type
des valeurs.
"""

import datetime
import uuid
from functools import cache
import os
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from google.protobuf.timestamp_pb2 import Timestamp

_CEL_SKIP = object()  # sentinel value


@cache
def get_app_timezone():
    """
    Fuseau horaire de l’application, lu dans la variable d’environnement TZ (UTC par défaut).
    """
    return ZoneInfo(os.environ.get("TZ") or "UTC")


def _to_timestamp(value: datetime.datetime) -> Timestamp:
    timestamp = Timestamp()
    timestamp.FromDatetime(value.astimezone(datetime.timezone.utc))
    return timestamp


def value_to_cel(value):
    """
    Convertit une valeur Python (scalaire, date, uuid, liste, dict) en valeur CEL. Retourne `_CEL_SKIP`
    si elle n’est pas représentable. Une instance de modèle n’est pas une valeur Python : utiliser
    `object_to_cel`.
    """
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, datetime.datetime):  # sous-classe de date : à tester en premier
        if value.tzinfo is None:
            value = value.replace(tzinfo=get_app_timezone())
        return _to_timestamp(value)
    if isinstance(value, datetime.date):
        midnight = datetime.datetime.combine(value, datetime.time(), tzinfo=get_app_timezone())
        return _to_timestamp(midnight)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            converted = value_to_cel(item)
            if converted is _CEL_SKIP:
                return _CEL_SKIP
            items.append(converted)
        return items
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        items = {}
        for key, item in value.items():
            converted = value_to_cel(item)
            if converted is _CEL_SKIP:
                return _CEL_SKIP
            items[key] = converted
        return items
    return _CEL_SKIP


def object_to_cel(instance) -> dict:
    """
    Convertit une instance de modèle (objet chargé par un store relationnel, ex. nomenclature) en objet
    CEL : un dict de ses colonnes, lues sans charger de relation (`fields.<nom>.<colonne>`). Les colonnes
    non représentables sont omises. Chaque colonne est convertie par `value_to_cel`.
    """
    state = sa.inspect(instance, raiseerr=False)
    if state is None or not hasattr(state, "mapper"):
        raise TypeError(f"object_to_cel attend une instance de modèle, reçu {type(instance)!r}")
    items = {}
    for attr in state.mapper.column_attrs:
        converted = value_to_cel(getattr(instance, attr.key))
        if converted is not _CEL_SKIP:
            items[attr.key] = converted
    return items
