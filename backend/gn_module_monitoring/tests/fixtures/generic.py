import pytest
from geonature.tests.fixtures import users
from geonature.utils.env import db
from pypnusershub.db.models import User
from utils_flask_sqla_geo.generic import GenericQueryGeo

from sqlalchemy import select
from flask import current_app
from pathlib import Path

import tempfile

from geonature.core.gn_permissions.models import (
    PermFilterType,
    PermAction,
    PermObject,
    Permission,
)
from geonature.core.gn_commons.models import TModules, TMedias, BibTablesLocation
from pypnusershub.db.models import (
    User,
    Organisme,
    Application,
    Profils as Profil,
    UserApplicationRight,
)


@pytest.fixture(scope="session")
def monitorings_users(app):
    app = db.session.execute(
        select(Application).where(Application.code_application == "GN")
    ).scalar_one()
    profil = db.session.execute(select(Profil).where(Profil.nom_profil == "Lecteur")).scalar_one()

    modules = db.session.scalars(select(TModules)).all()

    actions = {
        code: db.session.execute(
            select(PermAction).where(PermAction.code_action == code)
        ).scalar_one()
        for code in "CRUVED"
    }
    type_code_object = [
        "MONITORINGS_MODULES",
        "MONITORINGS_GRP_SITES",
        "MONITORINGS_SITES",
        "MONITORINGS_VISITES",
        "ALL",
    ]

    def create_user(username, organisme=None, scope=None, sensitivity_filter=False):
        # do not commit directly on current transaction, as we want to rollback all changes at the end of tests
        with db.session.begin_nested():
            user = User(
                groupe=False,
                active=True,
                organisme=organisme,
                identifiant=username,
                password=username,
            )
            db.session.add(user)
        # user must have been commited for user.id_role to be defined
        with db.session.begin_nested():
            # login right
            right = UserApplicationRight(
                id_role=user.id_role, id_application=app.id_application, id_profil=profil.id_profil
            )
            db.session.add(right)
            if scope > 0:
                for co in type_code_object:
                    object_all = db.session.scalars(
                        select(PermObject).where(PermObject.code_object == co)
                    ).all()
                    for action in actions.values():
                        for module in modules:
                            for obj in object_all + module.objects:
                                permission = Permission(
                                    role=user,
                                    action=action,
                                    module=module,
                                    object=obj,
                                    scope_value=scope if scope != 3 else None,
                                    sensitivity_filter=sensitivity_filter,
                                )
                                db.session.add(permission)
        return user

    users = {}

    organisme = Organisme(nom_organisme="Autre")
    db.session.add(organisme)

    users_to_create = [
        ("noright_user", organisme, 0),
        ("stranger_user", None, 2),
        ("associate_user", organisme, 2),
        ("self_user", organisme, 1),
        ("user", organisme, 2),
        ("admin_user", organisme, 3),
    ]

    for username, *args in users_to_create:
        users[username] = create_user(username, *args)

    return users
