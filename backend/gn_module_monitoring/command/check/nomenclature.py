from functools import cache

import click

from sqlalchemy import select
from marshmallow import ValidationError

from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.config.nomenclature import load_module_nomenclatures


@cache
def get_nomenclature_type(mnemonique):
    return db.session.execute(
        select(BibNomenclaturesTypes).where(BibNomenclaturesTypes.mnemonique == mnemonique)
    ).scalar_one_or_none()


@cache
def get_nomenclature(nomenclature_type, *whereclauses, **kwargs):
    if nomenclature_type is not None:
        whereclauses = (TNomenclatures.nomenclature_type == nomenclature_type, *whereclauses)
    return db.session.execute(
        select(TNomenclatures).where(
            *whereclauses,
            *[getattr(TNomenclatures, k) == v for k, v in kwargs.items()],
        )
    ).scalar_one_or_none()


def check_module_nomenclatures(module_code: str, check_data: bool, fix: bool):
    """
    Compare le fichier nomenclature.json du protocole avec les nomenclatures
    présentes en base.
    """
    try:
        nomenclatures = load_module_nomenclatures(module_code)
    except ValidationError as e:
        yield e
        return
    if nomenclatures is None:
        return
    if not check_data:
        return

    for nomenclature_type in nomenclatures["types"]:
        db_nomenclature_type = get_nomenclature_type(nomenclature_type["mnemonique"])
        if db_nomenclature_type is None:
            yield f"le type de nomenclature '{nomenclature_type['mnemonique']}' est manquant"
            if fix and click.confirm("Ajouter ?"):
                db.session.add(BibNomenclaturesTypes(**nomenclature_type))
                db.session.commit()
                get_nomenclature_type.cache_clear()
            continue
        for k, v in nomenclature_type.items():
            if getattr(db_nomenclature_type, k) != v:
                yield (
                    f"le type de nomenclature '{nomenclature_type['mnemonique']}' a été modifié\n"
                    f"attribut {click.style(k, bold=True)}\n"
                    f"{click.style('-', fg='red')} {v}\n"
                    f"{click.style(text='+', fg='green')} {getattr(db_nomenclature_type, k)}"
                )
                if fix and click.confirm("Modifier ?"):
                    setattr(db_nomenclature_type, k, v)
                    db.session.commit()

    for nomenclature in nomenclatures["nomenclatures"]:
        nomenclature_type_mnemonique = nomenclature.pop("type")
        db_nomenclature_type = get_nomenclature_type(nomenclature_type_mnemonique)
        if db_nomenclature_type is None:
            yield f"le type de nomenclature '{nomenclature_type_mnemonique}' n’existe pas"
            # TODO: list nomenclature types which contains a nomenclature with this cd_nomenclature?
            continue
        db_nomenclature = get_nomenclature(
            db_nomenclature_type, cd_nomenclature=nomenclature["cd_nomenclature"]
        )
        if db_nomenclature is None:
            yield f"la nomenclature '{nomenclature['cd_nomenclature']}' de type '{nomenclature_type_mnemonique}' est manquante"
            if fix:
                # TODO: add nomenclature directly?
                yield "\nPour corriger, lancer la commande 'geonature monitorings add_module_nomenclatures'"
            continue
        for k, v in nomenclature.items():
            if k == "type":
                continue
            if getattr(db_nomenclature, k) != v:
                yield (
                    f"la nomenclature '{nomenclature['cd_nomenclature']}' a été modifié\n"
                    f"attribut {click.style(k, bold=True)}\n"
                    f"{click.style('-', fg='red')} {v}\n"
                    f"{click.style(text='+', fg='green')} {getattr(db_nomenclature, k)}"
                )
                if fix and click.confirm("Modifier ?"):
                    setattr(db_nomenclature, k, v)
                    db.session.commit()
