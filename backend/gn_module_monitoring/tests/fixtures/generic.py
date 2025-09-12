from sqlalchemy import select
import pytest
from geonature.utils.env import db
from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)
from geonature.core.gn_commons.models import TModules

from pypnusershub.db.models import User
from pypnusershub.db.models import (
    User,
    Organisme,
    Application,
    Profils as Profil,
    UserApplicationRight,
)

from gn_module_monitoring.monitoring.models import TMonitoringModules


def add_user_permission(
    module_code, user, scope, type_code_object, code_action="CRUVED", sensitivity_filter=None
):
    """
    Add permissions to a user in a module.

    Parameters
    ----------
    module_code : str
        Code of the module to add the permission to.
    user : User
        User to add the permission to.
    scope : int
        Scope value for the permission.
    type_code_object : str
        Type of the object to add the permission to.
    code_action : str, optional
        Code of the action to add the permission for. Default is "CRUVED".

    Notes
    -----
    The function will add the permission to the specified module and object with the given scope.
    If the scope is 3, the scope_value will be set to None.
    """
    module = db.session.execute(
        select(TModules).where(TModules.module_code == module_code)
    ).scalar_one()
    actions = {
        code: db.session.execute(
            select(PermAction).where(PermAction.code_action == code)
        ).scalar_one()
        for code in code_action
    }
    with db.session.begin_nested():
        if scope > 0:
            object_all = db.session.scalars(
                select(PermObject).where(PermObject.code_object == type_code_object)
            ).all()
            for action in actions.values():
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


@pytest.fixture(scope="session")
def create_user():
    def _create_user(
        username,
        organisme=None,
        scope=None,
        sensitivity_filter=False,
        modules=None,
    ):
        app = db.session.execute(
            select(Application).where(Application.code_application == "GN")
        ).scalar_one()
        profil = db.session.execute(
            select(Profil).where(Profil.nom_profil == "Lecteur")
        ).scalar_one()

        if not modules:
            modules = db.session.scalars(select(TModules)).all()

        type_code_object = [
            "MONITORINGS_MODULES",
            "MONITORINGS_GRP_SITES",
            "MONITORINGS_SITES",
            "MONITORINGS_VISITES",
            "ALL",
        ]

        # do not commit directly on current transaction, as we want to rollback all changes at the end of tests
        with db.session.begin_nested():
            user = User(
                groupe=False,
                active=True,
                organisme=organisme,
                identifiant=username,
                password=username,
                nom_role=username,
                prenom_role=username,
            )
            db.session.add(user)
        # user must have been commited for user.id_role to be defined
        with db.session.begin_nested():
            # login right
            right = UserApplicationRight(
                id_role=user.id_role, id_application=app.id_application, id_profil=profil.id_profil
            )
            db.session.add(right)

        for module in modules:
            for code_object in type_code_object:
                add_user_permission(
                    module.module_code,
                    user,
                    scope,
                    code_object,
                    code_action="CRUVED",
                    sensitivity_filter=sensitivity_filter,
                )

        return user

    return _create_user


@pytest.fixture()
def create_test_module_user(install_module_test, create_user):
    """user with right to read MONITORINGS_SITES of the test module because he is the digitiser of the sites"""

    def _create_test_module_user():
        module = db.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        ).scalar()
        return create_user("test_module_user", scope=1, modules=[module])

    return _create_test_module_user


@pytest.fixture()
def test_module_user(create_test_module_user):
    return create_test_module_user()
