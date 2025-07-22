from sqlalchemy import select

from geonature.utils.env import db
from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)
from geonature.core.gn_commons.models import TModules


def add_user_permission(module_code, user, scope, type_code_object, code_action="CRUVED"):
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
                        sensitivity_filter=None,
                    )
                    db.session.add(permission)
