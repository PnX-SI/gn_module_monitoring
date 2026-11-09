from functools import cache

from sqlalchemy import select

from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.tools.utils import schema_context


@cache
def get_nomenclature_type(mnemonique):
    return db.session.execute(
        select(BibNomenclaturesTypes).where(BibNomenclaturesTypes.mnemonique == mnemonique)
    ).scalar_one_or_none()


def get_declared_nomenclatures():
    """
    Nomenclatures déclarées dans le nomenclature.json du module du contexte (types et nomenclatures),
    qu’elles soient ou non présentes en base.
    """
    module = schema_context.get()["module"]
    return module.nomenclatures


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
