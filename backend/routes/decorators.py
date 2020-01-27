"""
    Ce module définie un décorateur qui prend en compte les modules de suivi générique
"""

from flask import request
from functools import wraps
from pypnusershub.db.tools import InsufficientRightsError

from geonature.core.gn_permissions.tools import (
    get_user_from_token_and_raise,
    cruved_scope_for_user_in_module
)

from ..modules.repositories import get_module


def to_int(s):
    try:
        return int(s)
    except ValueError:
        return None


def to_int_cruved(cruved):
    for key in cruved:
        cruved[key] = to_int(cruved[key])
    return cruved


def cruved_scope_for_user_in_monitoring_module(module_path=None):
    user = get_user_from_token_and_raise(request)

    cruved_module = {
        'C': '0',
        'R': '0',
        'U': '0',
        'V': '0',
        'E': '0',
        'D': '0'
    }

    # If user not a dict: its a token issue
    # return the appropriate Response
    if not isinstance(user, dict):
        return user

    # get_monitoring from route parameter monitoring_url
    module = None
    herited = False

    if module_path and module_path != 'null':
        module = get_module('module_path', module_path)
        if module:
            cruved_module, herited = cruved_scope_for_user_in_module(user['id_role'], module.module_code, 'ALL')
            if not herited:
                return to_int_cruved(cruved_module)

    cruved_monitorings, herited = cruved_scope_for_user_in_module(user['id_role'], 'MONITORINGS', 'ALL')
    if not herited:
        return to_int_cruved(cruved_monitorings)

    # return cruved_0, user
    return to_int_cruved(cruved_monitorings)


def check_cruved_scope_monitoring(
    action,
    droit_min=1,
    redirect_on_expiration=None,
    redirect_on_invalid_token=None
):
    """
        Decorateur qui verifie si un utilisateur a des droit sur un module de suivi
        (reférencé dans la route comme module_path)

        Prend en compte le droit maximum entre le module MONITORINGS et le module spécifique
        autorise l'acces a la route si ce droit est supérieur ou égal à droit_min

        :params action: type d'action CRUVED
        :param droit min: droit minimum pour acceder a la route
        :param redirect_on_expiration: url en cas d'expiration
        :param redirect_on_invalid_token: url en cas de token invalid
        :param return_module: si vrai rajoute le module en parametre de route
        :type action: str
        :type droit: int
        :type redirect_on_expiration: str
        :type redirect_on_invalid_token: str
        :type return_module: bool
    """

    def _check_cruved_scope_monitoring(fn):
        @wraps(fn)
        def __check_cruved_scope_monitoring(*args, **kwargs):

            module_path = kwargs.get('module_path')

            cruved = cruved_scope_for_user_in_monitoring_module(module_path)
            user = get_user_from_token_and_raise(request)
            permission = cruved[action]

            if not permission or permission < droit_min:
                raise InsufficientRightsError(
                    '''User {} with permission level {} for action {} \
is not allowed to use this route for module {}, \
min permission level is {}'''.format(
                        user['id_role'],
                        permission,
                        action,
                        module_path or 'monitorings',
                        droit_min
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return __check_cruved_scope_monitoring

    return _check_cruved_scope_monitoring
