'''
    module pour faire des test en tout genre
'''

from flask import request, current_app
from flask import url_for
from utils_flask_sqla.response import json_resp

from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.gn_permissions.tools import get_user_from_token_and_raise
from geonature.core.gn_permissions.tools import cruved_scope_for_user_in_module

from ..utils.env import MODULE_MONITORINGS_CODE
from geonature.utils.env import DB

from ..monitoring.models import (
    TMonitoringModules
)

from ..blueprint import blueprint


@blueprint.route('/routes_list', methods=['GET'])
@check_cruved_scope('R', module_code=MODULE_MONITORINGS_CODE)
@json_resp
def get_route_list():
    '''
        retourne la liste des routes du module
    '''

    s_filter = request.args.get("filter")

    rules = current_app.url_map.iter_rules()
    if s_filter:
        rules = filter(lambda x: s_filter in str(x), current_app.url_map.iter_rules())
    # module_url = current_app.config[MODULE_MONITORINGS_CODE]['MODULE_URL']
    # rules = filter(lambda x: module_url in str(x), current_app.url_map.iter_rules())

    out = []

    for rule in rules:
        methods = [x for x in rule.methods if x not in ['OPTIONS', 'HEAD']][0].ljust(8)
        o = {'url': str(rule), 'methods': str(methods)}
        out.append(o)
    sorted(out, key=lambda x: str(x['url']))
    return [o['methods'] + ' ' + o['url'] for o in out]


@blueprint.route('/test_permission', methods=['GET'])
@json_resp
def test_permission():
    '''
        tests sur les permissions
    '''
    user = get_user_from_token_and_raise(request)
    id_role = user['id_role']
    cruved_monitoring = cruved_scope_for_user_in_module(id_role, MODULE_MONITORINGS_CODE, "ALL")
    cruved_test = cruved_scope_for_user_in_module(id_role, 'TEST', "ALL")
    return {
        'cruved_test': cruved_test,
        'cruved_monitoring': cruved_monitoring,
    }


@blueprint.route('/test_static', methods=['GET'])
@json_resp
def test_static():
    return url_for('static', filename='medias/1/31_dead.letter')


@blueprint.route('test/models/<int:depth>', methods=['GET'])
@json_resp
def test_model(depth):

    modules = DB.session.query(TMonitoringModules).all()
    return [module.as_dict(depth=depth) for module in modules]
    # recursif = True
    # return [module.as_dict(recursif=recursif) for module in modules]
