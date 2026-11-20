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


def build_schema_rows(df: pd.DataFrame, entity_code: str, entity) -> list[dict]:
    """
    Retourne, pour chaque ligne de `df`, le dictionnaire d'entrée de `entity.get_extended_schema()`.

    La liste est dans le même ordre que `df.index` : la position `i` correspond à `df.index[i]`.
    Les valeurs sont lues dans les colonnes `dest_column` des champs (valeurs typées par
    `check_types`) ; une colonne absente de `df` ne produit pas de clé. Les colonnes qui ne sont pas importées
    (voir `build_field_names`) sont ignorées.
    """
    names = build_field_names(entity_code, entity)
    # Pour les champs monitoring, `dest_field` vaut l'import field name (`prepare_fields`)
    present = [
        (import_field_name, entity_field_name)
        for import_field_name, entity_field_name in names.import_to_entity.items()
        if import_field_name in df.columns
    ]
    records = df[[import_field_name for import_field_name, _ in present]].to_dict("records")

    rows = []
    for record in records:
        row = {}
        for import_field_name, entity_field_name in present:
            row[entity_field_name] = _to_python_value(record[import_field_name])
        rows.append(row)
    return rows
