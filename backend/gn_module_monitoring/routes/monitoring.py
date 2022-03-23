'''
    module definissant les routes d'accès de modification des objects
        site, visit, observation, ...
'''


from flask import request, send_from_directory, url_for
from utils_flask_sqla.response import (
    json_resp, json_resp_accept_empty_list
)

from ..blueprint import blueprint

from .decorators import check_cruved_scope_monitoring

# from geonature.utils.errors import GeoNatureError
from ..monitoring.definitions import monitoring_definitions
from ..modules.repositories import get_module
from ..utils.utils import to_int
from ..config.repositories import get_config
from utils_flask_sqla_geo.generic import GenericTableGeo
from geonature.utils.env import DB, ROOT_DIR
import datetime as dt
from utils_flask_sqla.response import to_csv_resp, to_json_resp
from utils_flask_sqla.generic import serializeQuery
import geonature.utils.filemanager as fm
from pathlib import Path




@blueprint.route('/object/<string:module_code>/<string:object_type>/<int:id>', methods=['GET'])
@blueprint.route(
    '/object/<string:module_code>/<string:object_type>',
    defaults={'id': None},
    methods=['GET'])
@blueprint.route(
    '/object/module',
    defaults={'module_code': None, 'object_type': 'module', 'id': None},
    methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp
def get_monitoring_object_api(module_code, object_type, id):
    '''
        renvoie un object, à partir de type de l'object et de son id

        :param module_code: reference le module concerne
        :param object_type: le type d'object (site, visit, obervation)
        :param id : l'identifiant de l'object (de id_base_site pour site)
        :type module_code: str
        :type object_type: str
        :type id: int

        :return: renvoie l'object requis
        :rtype: dict
    '''

    # field_name = param.get('field_name')
    # value = module_code if object_type == 'module'
    get_config(module_code, force=True)

    depth = to_int(request.args.get('depth', 1))

    return (
        monitoring_definitions
        .monitoring_object_instance(module_code, object_type, id)
        .get(depth=depth)
        # .get(value=value, field_name = field_name)
        .serialize(depth)
    )


def create_or_update_object_api(module_code, object_type, id):
    '''
        route pour la création ou la modification d'un objet
        si id est renseigné, c'est une création (PATCH)
        sinon c'est une modification (POST)

        :param module_code: reference le module concerne
        :param object_type: le type d'object (site, visit, obervation)
        :param id : l'identifiant de l'object (de id_base_site pour site)
        :type module_code: str
        :type object_type: str
        :type id: int
        :return: renvoie l'object crée ou modifié
        :rtype: dict
    '''
    depth = to_int(request.args.get('depth', 1))

    # recupération des données post
    post_data = dict(request.get_json())
    module = get_module('module_code', module_code)

    # on rajoute id_module s'il n'est pas renseigné par défaut ??
    post_data['properties']['id_module'] = module.id_module

    return (
        monitoring_definitions.monitoring_object_instance(module_code, object_type, id)
        .create_or_update(post_data)
        .serialize(depth)
    )

# update object
@blueprint.route('object/<string:module_code>/<object_type>/<int:id>', methods=['PATCH'])
@blueprint.route(
    '/object/<string:module_code>/module',
    defaults={'id': None, 'object_type': 'module'},
    methods=['PATCH'])
@check_cruved_scope_monitoring('U', 1)
@json_resp
def update_object_api(module_code, object_type, id):
    get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type, id)


# create object
@blueprint.route('object/<string:module_code>/<object_type>', defaults={'id': None}, methods=['POST'])
@blueprint.route(
    '/object/module',
    defaults={'module_code': None, 'object_type': 'module', 'id': None},
    methods=['POST'])
@check_cruved_scope_monitoring('C', 1)
@json_resp
def create_object_api(module_code, object_type, id):
    get_config(module_code, force=True)
    return create_or_update_object_api(module_code, object_type, id)


# delete
@blueprint.route('object/<string:module_code>/<object_type>/<int:id>', methods=['DELETE'])
@blueprint.route(
    '/object/<string:module_code>/module',
    defaults={'id': None, 'object_type': 'module'},
    methods=['DELETE'])
@check_cruved_scope_monitoring('D', 3)
@json_resp
def delete_object_api(module_code, object_type, id):

    get_config(module_code, force=True)

    return (
        monitoring_definitions
        .monitoring_object_instance(module_code, object_type, id)
        .delete()
    )


# breadcrumbs
@blueprint.route('breadcrumbs/<string:module_code>/<object_type>/<int:id>', methods=['GET'])
@blueprint.route('breadcrumbs/<string:module_code>/<object_type>',
    defaults={'id': None},
    methods=['GET']
)
@blueprint.route(
    '/breadcrumbs/<string:module_code>/module',
    defaults={'id': None, 'object_type': 'module'},
    methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp
def breadcrumbs_object_api(module_code, object_type, id):

    get_config(module_code, force=True)
    query_params = dict(**request.args)
    query_params['parents_path'] =  request.args.getlist('parents_path')
    return (
        monitoring_definitions
        .monitoring_object_instance(module_code, object_type, id)
        .get()
        .breadcrumbs(query_params)
    )


# listes pour les formulaires par exemple
@blueprint.route('list/<string:module_code>/<object_type>', methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
@json_resp_accept_empty_list
def list_object_api(module_code, object_type):

    get_config(module_code, force=True)

    return (
        monitoring_definitions
        .monitoring_object_instance(module_code, object_type)
        .get_list(request.args)
    )


# mise à jour de la synthèse
@blueprint.route('synthese/<string:module_code>', methods=['POST'])
@check_cruved_scope_monitoring('E', 3)
@json_resp
def update_synthese_api(module_code):

    get_config(module_code, force=True)

    return (
        monitoring_definitions
        .monitoring_object_instance(module_code, 'module')
        .get()
        .process_synthese(process_module=True)
    )
# export add mje
# export all observations
@blueprint.route('/exports/csv/<module_code>/<type>/<method>/<jd>', methods=['GET'])
@check_cruved_scope_monitoring('R', 1)
def export_all_observations(module_code, type, method,jd):
    """
    Export all the observations made on a site group.
    Following formats are available:
    * csv
    * geojson
    * shapefile
    """

    view = GenericTableGeo(
        tableName="v_export_" + module_code.lower()+"_"+method,
        schemaName="gn_monitoring",
        engine=DB.engine

    )
    columns = view.tableDef.columns
    q = DB.session.query(*columns)
    if "dataset" in columns:
        data =q.filter(columns.id_dataset == jd)
    data = q.all()
    filename = module_code+"_"+method+"_"+dt.datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S")

    if type == 'csv':
        return to_csv_resp(
            filename,
            data=serializeQuery(data, q.column_descriptions),
            separator=";",
            columns=[db_col.key for db_col in columns if db_col.key != 'geom'], # Exclude the geom column from CSV
        )
    else:
        raise NotFound("type export not found")


@blueprint.route('/exports/pdf/<module_code>/<object_type>/<int:id>', methods=['POST'])
def post_export_pdf(module_code, object_type, id):
    """
    Export the fiche individu as a PDF file.
    Need to push the map image in the post data to be present in PDF.
    Need to set a template in sub-module.
    """

    depth = to_int(request.args.get('depth', 0))
    monitoring_object= (
        monitoring_definitions
        .monitoring_object_instance(module_code, object_type, id
        ).get()
        .serialize(depth)
    )

    df = {
        'module_code': module_code,
        'monitoring_object': monitoring_object,
        'extra_data': request.json['extra_data'],
        # 'static_pdf_dir': "static/external_assets/monitorings/{}/exports/pdf/".format(module_code),
        'static_pdf_dir': url_for('static', filename="external_assets/monitorings/{}/exports/pdf/".format(module_code)),
        'map_image': request.json['map']

    }

    template = request.json['template']

    pdf_file = fm.generate_pdf(
        "modules/monitorings/{}/{}".format(module_code, template),
        df,
        "map_area.pdf"
    )
    pdf_file_posix = Path(pdf_file)
    try:
	    return send_from_directory(str(pdf_file_posix.parent), pdf_file_posix.name, as_attachment=True)
    except Exception as e:
	    return str(e)