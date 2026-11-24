"""
Construction des lignes d'entrée du schéma étendu d'une entité, à partir du DataFrame traité
à l'import.

Chaque ligne est un dictionnaire dont les clés sont les noms de configuration des champs
(`entity.data["fields"]`), tels qu'attendus par `entity.get_extended_schema()`. Les champs
supplémentaires (non natifs) sont passés à plat, comme l'API : le schéma les regroupe lui-même
dans `data`. Une clé `data` imbriquée serait remplacée par le schéma et ses valeurs perdues.

Les valeurs absentes (`NaN`, `NaT`, `pd.NA`, `None`, chaîne vide) deviennent `None`. Les valeurs
pandas et numpy sont converties en types Python natifs.
"""

import numpy as np
import pandas as pd

from gn_module_monitoring.monitoring.import_actions.field_names import (
    build_field_names,
)
from gn_module_monitoring.tools.stores.type import GeometryStore


def _to_python_value(value):
    if pd.api.types.is_scalar(value) and pd.isna(value):
        return None
    if isinstance(value, str):
        return value if value != "" else None
    if isinstance(value, np.datetime64):
        value = pd.Timestamp(value)
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and value.is_integer():
        # Une colonne d'entiers contenant une valeur absente est lue en float : 3.0 -> 3
        return int(value)
    return value


def _read_column(import_field_name: str, entity_field_name: str, entity) -> str:
    """Colonne du DataFrame lue pour un champ : le WKT source pour une géométrie, sinon `dest_column`."""
    store = entity.data["fields"][entity_field_name]["store"]
    if isinstance(store, GeometryStore):
        return f"src_{import_field_name}"
    return import_field_name


def build_schema_rows(df: pd.DataFrame, entity_code: str, entity) -> list[dict]:
    """
    Retourne, pour chaque ligne de `df`, le dictionnaire d'entrée de `entity.get_extended_schema()`.

    La liste est dans le même ordre que `df.index` : la position `i` correspond à `df.index[i]`.
    Les valeurs sont lues dans les colonnes `dest_column` des champs (valeurs typées par
    `check_types`) ; une colonne absente de `df` ne produit pas de clé. Les colonnes qui ne sont pas importées
    (voir `build_field_names`) sont ignorées.
    Un champ géométrie n'a pas encore de colonne `dest_column` à ce stade : son WKT source
    (`source_column`, `src_<import field name>`) est lu à la place.
    """
    names = build_field_names(entity_code, entity)
    # Pour les champs monitoring, `dest_field` vaut l'import field name (`prepare_fields`)
    present = []
    for import_field_name, entity_field_name in names.import_to_entity.items():
        column = _read_column(import_field_name, entity_field_name, entity)
        if column in df.columns:
            present.append((column, entity_field_name))
    records = df[[column for column, _ in present]].to_dict("records")

    rows = []
    for record in records:
        row = {}
        for column, entity_field_name in present:
            row[entity_field_name] = _to_python_value(record[column])
        rows.append(row)
    return rows
