'''
    routes pour les modules de suivis...
'''

from flask import request
from utils_flask_sqla.response import json_resp_accept_empty_list, json_resp

from ..blueprint import blueprint
from ..routes.decorators import check_cruved_scope_monitoring
from ..utils.utils import to_int

from ..modules.repositories import (
    get_module,
    get_modules,
)


@blueprint.route('/module/<value>', methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp
def get_module_api(value):
    '''
        Renvoie un module référencé par son champ module_path
        par default cherche par id_module
        on peut preciser field_name en parametre de requete GET
        ?field_name=module_path pour avoir unmodule depuis son champs module_path
    '''

    depth = to_int(request.args.get('depth', False))
    field_name = request.args.get('field_name', 'id_module')

    module = get_module(field_name, value)

    return module and module.as_dict(depth=depth)


@blueprint.route('/modules', methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp_accept_empty_list
def get_modules_api():
    '''
        Renvoie la liste des modules de suivi
    '''

    depth = request.args.get('depth')

    modules = get_modules()
    return [module.as_dict(depth=depth) for module in modules]
