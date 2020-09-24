import os
import json

from sqlalchemy import and_

from geonature.core.gn_commons.models import BibTablesLocation
from geonature.utils.errors import GeoNatureError
from geonature.utils.env import DB

# chemin ver le repertoire de la config
CONFIG_PATH = os.path.dirname(os.path.abspath(
    __file__)) + '/../../config/monitoring'


def get_id_table_location(object_type):

    table_names = {
        'module': 't_module_complements',
        'site': 't_base_sites',
        'visit': 't_base_visits',
        'observation': 't_observations'
    }

    schema_name = 'gn_monitoring'
    table_name = table_names.get(object_type)

    if not table_name:
        return None

    id_table_location = None

    try:
        id_table_location = (
            DB.session.query(BibTablesLocation.id_table_location)
            .filter(
                and_(
                    BibTablesLocation.schema_name == schema_name,
                    BibTablesLocation.table_name == table_name
                )
            )
            .one()
        )[0]
    except Exception as e:
        print(schema_name, table_name, e)
        pass

    return id_table_location


def copy_dict(dict_in):
    return json.loads(json.dumps(dict_in))


def keys_remove_doublons(dict1, dict2):
    return list(dict.fromkeys(list(dict1.keys()) + list(dict2.keys())))


def json_from_file(file_path, result_default):
    '''
        get json content from a json file

        :param file_path: chemin absolu vers le fichier
        :param result_default: resultat par defaut, renvoyé si le fichier n'existe pas ([], None, {})
        :type file_path : str
        :type result_default: dict | list
        :return: default result if file does not exists
        :rtype: dict | list
    '''
    out = result_default
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                out = json.load(f)
    except Exception as e:
        pass
        raise GeoNatureError(
            "Module monitoring - Config - error in file {} : {}"
            .format(file_path, str(e))
        )
    return out


def json_config_from_file(module_path, type_config):

    file_path = "{}/{}/{}.json".format(CONFIG_PATH, module_path, type_config)
    return json_from_file(file_path, {})


def json_schema_from_file(module_path, object_type):

    file_path = "{}/{}/schema_{}.json".format(CONFIG_PATH, module_path, object_type)
    return json_from_file(file_path, {})


def config_from_files(config_type, module_path):

    generic_config_custom = json_config_from_file('generic', config_type)
    specific_config_custom = {} if module_path == 'generic' else json_config_from_file(module_path, config_type)

    generic_config_custom.update(specific_config_custom)

    return generic_config_custom


def directory_last_modif(dir_path):
    '''
        get the last modification time among all file in a directory

        :param dir_path: absolute path to the directory
        :type dir_path: str
        :return: last modification time
        :rtype: float
    '''
    modification_time_max = 0
    for (repertoire, sousRepertoires, fichiers) in os.walk(dir_path, followlinks=True):
        for fichier in fichiers:
            modification_time = os.path.getmtime(repertoire + '/' + fichier)
            if modification_time > modification_time_max:
                modification_time_max = modification_time

    return modification_time_max


def schema_dict_to_array(schema_dict):

    schema_array = []

    for key in schema_dict:
        elem = schema_dict[key]
        elem['attribut_name'] = key
        schema_array.append(elem)

    return schema_array


def process_schema(object_type, config):

    generic = config[object_type]['generic']

    # specific n'est pas toujours defini
    if not config[object_type].get('specific'):
        config[object_type]['specific'] = {}
    specific = config[object_type]['specific']

    # generic redef in specific
    #  cas ou un element de generic est redefini dans specific
    keys_s = list(specific.keys())
    keys_g = list(generic.keys())
    for key_s in keys_s:
        for key_g in keys_g:
            if key_s == key_g:
                key = key_s

                type_widget_s = specific[key].get('type_widget')
                type_widget_g = generic[key].get('type_widget')

                if type_widget_s and type_widget_s == type_widget_g:
                    generic[key] = copy_dict(specific[key])
                else:
                    generic[key].update(copy_dict(specific[key]))

                del specific[key]


def process_config_display(object_type, config):

    config_object = config[object_type]

    schema = dict(config_object['generic'])
    schema.update(config_object['specific'])

    properties_keys = list(schema.keys())

    display_properties = config_object.get(
        'display_properties',
        [key for key in schema if not schema[key].get('hidden')]
    )

    display_list = config_object.get(
        'display_list',
        display_properties
    )

    config_object['display_properties'] = display_properties
    config_object['display_list'] = display_list
    config_object['properties_keys'] = properties_keys


def customize_config(elem, custom):

    if isinstance(elem, list):
        elem = [customize_config(e, custom) for e in elem]
        # patch remove doublons
        if len(elem) and not isinstance(elem[0], dict):
            elem = list(dict.fromkeys(elem))

    elif isinstance(elem, dict):
        for key in elem:
            elem[key] = customize_config(elem[key], custom)

    elif elem in custom:
        elem = custom[elem]

    return elem


def config_from_files_customized(type_config, module_path):
    config_type = config_from_files(type_config, module_path)
    custom = config_from_files('custom', module_path)
    return customize_config(config_type, custom)
