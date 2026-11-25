"""
Mappings de l'import, exécutés avant la validation par schéma étendu (hook `check_pre` de chaque entité).

Ils écrivent dans les colonnes de destination de la table transitoire les valeurs que les stores attendent
(identifiants). Les mappings sont propres à l'import : les stores ne les connaissent pas.
"""

import sqlalchemy as sa

from geonature.core.imports.models import BibFields, TImports
from geonature.utils.env import db


def map_observers_to_dest(imprt: TImports, observer_field: BibFields) -> None:
    """
    Observateurs de la colonne source (noms séparés par des virgules) -> tableau d'`id_role` dans la colonne
    de destination, via `observermapping`. Un nom non résolu donne NULL dans le tableau : le store le signale.
    """
    transient_table = imprt.destination.get_transient_table()
    source = transient_table.c[observer_field.source_column]
    mapping = imprt.observermapping or {}

    values = db.session.scalars(
        sa.select(sa.distinct(source)).where(
            transient_table.c.id_import == imprt.id_import,
            source.isnot(None),
        )
    ).all()
    for value in values:
        ids = []
        for name in value.split(","):
            name = name.strip()
            if not name:
                continue
            mapped = mapping.get(name)
            ids.append(mapped["id_role"] if mapped else None)
        db.session.execute(
            sa.update(transient_table)
            .where(transient_table.c.id_import == imprt.id_import, source == value)
            .values({observer_field.dest_column: ids})
        )
