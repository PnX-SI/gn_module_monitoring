from functools import cache

import sqlalchemy as sa
from sqlalchemy import select
from marshmallow import ValidationError

from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.tools.utils import schema_context


def validate_observers_in_list(roles, user_list):
    """
    Vérifie que chaque rôle (utilisateur) appartient à la liste d’observateurs `user_list`
    (utilisateurs.t_listes), via la vue v_userslist_forall_menu.
    """
    from geonature.core.users.models import VUserslistForallMenu

    allowed_ids = set(
        db.session.scalars(
            sa.select(VUserslistForallMenu.id_role).where(
                VUserslistForallMenu.id_menu == user_list.id_liste
            )
        ).all()
    )
    not_in_list = [role.id_role for role in roles if role.id_role not in allowed_ids]
    if not_in_list:
        raise ValidationError(
            f"Utilisateurs {not_in_list} absents de la liste d’observateurs '{user_list.code_liste}'."
        )


def validate_areas_of_type(areas, area_type):
    """
    Vérifie que chaque zone appartient au type de zone `area_type` (ref_geo.bib_areas_types).
    """
    not_of_type = [area.id_area for area in areas if area.id_type != area_type.id_type]
    if not_of_type:
        raise ValidationError(
            f"Zones {not_of_type} n’appartenant pas au type de zone '{area_type.type_code}'."
        )


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
