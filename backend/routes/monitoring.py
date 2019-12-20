'''
    module definissant les routes d'accès de modification des objects
        site, visit, observation, ...
'''

from flask import request

from utils_flask_sqla.response import (
    json_resp,
)

from ..blueprint import blueprint

from .decorators import check_cruved_scope_monitoring

# from geonature.utils.errors import GeoNatureError
from ..monitoring.definitions import monitoring_definitions
from ..utils.utils import to_int


@blueprint.route('/object/<string:module_path>/<string:object_type>/<int:id>', methods=['GET'])
@blueprint.route(
    '/object/<string:module_path>/<string:object_type>',
    defaults={'id': None},
    methods=['GET'])
@blueprint.route(
    '/object/module',
    defaults={'module_path': None, 'object_type': 'module', 'id': None},
    methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp
def get_monitoring_object_api(module_path, object_type, id):
    '''
        renvoie un object, à partir de type de l'object et de son id

        :param module_path: reference le module concerne
        :param object_type: le type d'object (site, visit, obervation)
        :param id : l'identifiant de l'object (de id_base_site pour site)
        :type module_path: str
        :type object_type: str
        :type id: int

        :return: renvoie l'object requis
        :rtype: dict
    '''

    # field_name = param.get('field_name')
    # value = module_path if object_type == 'module'

    depth = to_int(request.args.get('depth', 1))

    return (
        monitoring_definitions.monitoring_object_instance(module_path, object_type, id)
        .get()
        # .get(value=value, field_name = field_name)
        .serialize(depth)
    )


def create_or_update_object_api(module_path, object_type, id, module):
    '''
        route pour la création ou la modification d'un objet
        si id est renseigné, c'est une création (PATCH)
        sinon c'est une modification (POST)

        :param module_path: reference le module concerne
        :param object_type: le type d'object (site, visit, obervation)
        :param id : l'identifiant de l'object (de id_base_site pour site)
        :type module_path: str
        :type object_type: str
        :type id: int
        :return: renvoie l'object crée ou modifié
        :rtype: dict
    '''
    depth = to_int(request.args.get('depth', 1))

    # recupération des données post
    post_data = dict(request.get_json())

    # patch module id???
    if depth:
        post_data['properties']['id_module'] = module['id_module']

    return (
        monitoring_definitions.monitoring_object_instance(module_path, object_type, id)
        .create_or_update(post_data)
        .serialize(depth)
    )

# update object
@blueprint.route('object/<string:module_path>/<object_type>/<int:id>', methods=['PATCH'])
@blueprint.route(
    '/object/<string:module_path>/module',
    defaults={'id': None, 'object_type': 'module'},
    methods=['PATCH'])
@check_cruved_scope_monitoring('U', 1, return_module=True)
@json_resp
def update_object_api(module_path, object_type, id, module):
    return create_or_update_object_api(module_path, object_type, id, module)


# create object
@blueprint.route('object/<string:module_path>/<object_type>', defaults={'id': None}, methods=['POST'])
@blueprint.route(
    '/object/module',
    defaults={'module_path': None, 'object_type': 'module', 'id': None},
    methods=['POST'])
@check_cruved_scope_monitoring('C', 1, return_module=True)
@json_resp
def create_object_api(module_path, object_type, id, module):
    return create_or_update_object_api(module_path, object_type, id, module)


# delete
@blueprint.route('object/<string:module_path>/<object_type>/<int:id>', methods=['DELETE'])
@blueprint.route(
    '/object/<string:module_path>/module',
    defaults={'id': None, 'object_type': 'module'},
    methods=['DELETE'])
@check_cruved_scope_monitoring('D', 3)
@json_resp
def delete_object_api(module_path, object_type, id):

    return (
        monitoring_definitions
        .monitoring_object_instance(module_path, object_type, id)
        .delete()
    )


# breadcrumps
@blueprint.route('breadcrumps/<string:module_path>/<object_type>/<int:id>', methods=['GET'])
@blueprint.route(
    '/breadcrumps/<string:module_path>/module',
    defaults={'id': None, 'object_type': 'module'},
    methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp
def breadcrumps_object_api(module_path, object_type, id):

    return (
        monitoring_definitions
        .monitoring_object_instance(module_path, object_type, id)
        .get()
        .breadcrumps()
    )


@blueprint.route('circuit_points/<int:id_circuit>', methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp
def circuit_point_api(id_circuit):

    circuit = (
        monitoring_definitions
        .monitoring_object_instance('cheveches', 'circuit', id_circuit)
        .get()
        .serialize(depth=1)
    )

    circuit_points = circuit['children']['circuit_point']

    return circuit_points
