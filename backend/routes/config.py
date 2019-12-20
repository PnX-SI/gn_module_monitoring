from flask import request

from utils_flask_sqla.response import json_resp

from ..blueprint import blueprint
from ..config.repositories import (
    get_config,
    get_config_frontend
)
# from ..decorators import check_cruved_scope_monitoring


@blueprint.route('/config/<string:module_path>', methods=['GET'])
@blueprint.route('/config', defaults={'module_path': None}, methods=['GET'])
# @check_cruved_scop e_monitoring('R', 1)
@json_resp
def get_config_api(module_path):
    """
        route qui renvoie la config pour un module donné
    """

    return get_config_frontend(module_path)


@blueprint.route('/config/test/<string:module_path>', methods=['GET'])
# @check_cruved_scope_monitoring('R', 1)
@json_resp
def get_config_object_api(module_path):
    """
        route qui renvoie la config pour un module donné et un object donné (pour debug)
    """

    config = get_config(module_path)

    object_type = request.args.get('object_type')
    config_type = request.args.get('config_type')

    out = config

    if object_type:
        out = {
            'schema': config.get('schemas', {}).get(object_type),
            'object': config.get('objects', {}).get(object_type)
        }

    if config_type:
        out = config.get(config_type)

    return out


@blueprint.route('/config/test_tree/<string:module_path>', methods=['GET'])
# @check_cruved_scope_monitoring('R', 1)
@json_resp
def test_config_tree_api(module_path):

    config = get_config(module_path)

    config_objects = config.get('objects')

    d = {
            (key):
            (
                {
                    'parent_type': value.get('parent_type'),
                    'children_type': value.get('children_types'),
                }
                if key != 'tree' else None
            )
            for key, value in config_objects.items()
    }

    return d


@blueprint.route('/config/test_data/<string:module_path>', methods=['GET'])
# @check_cruved_scope_monitoring('R', 1)
@json_resp
def test_config_data_api(module_path):

    config = get_config(module_path)

    return config['data_utils']['taxonomy']
