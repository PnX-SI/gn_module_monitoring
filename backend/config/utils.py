import os
import json

from geonature.utils.errors import GeoNatureError


# chemin ver le repertoire de la config
CONFIG_PATH = os.path.dirname(os.path.abspath(
    __file__)) + '/../../config/monitoring'


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
            .format(file_path, e)
        )
    return out


def json_config_from_file(module_path, type_config):

    file_path = "{}/{}/config_{}.json".format(CONFIG_PATH, module_path, type_config)
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
    for (repertoire, sousRepertoires, fichiers) in os.walk(dir_path):
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


def process_schema(generic, specific):

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


def process_config_display(config):

    config_objects = config.get('objects')
    schemas = config.get('schemas')

    object_types = list(config_objects.keys())
    object_types.remove('tree')

    for object_type in object_types:
        schema = schemas[object_type]['generic'] + \
            schemas[object_type]['specific']

        display_properties = config_objects.get(
            object_type, {}).get('display_properties')
        if not display_properties:
            display_properties = [elem['attribut_name']
                                  for elem in schema if not elem.get('hidden')]

        display_list = config_objects.get(
            object_type, {}).get('display_list')
        if not display_list:
            display_list = display_properties

        config_objects[object_type]['display_properties'] = display_properties
        config_objects[object_type]['display_list'] = display_list

        properties_keys = [elem['attribut_name'] for elem in schema]
        for key in display_properties + display_list:
            if key not in properties_keys:
                properties_keys.append(key)

        config_objects[object_type]['properties_keys'] = properties_keys


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


def process_config_tree(objects, tree=None, parent_type=None):

    if not tree and not parent_type:
        tree = objects['tree']

    for object_type in tree.keys():

        children_types = tree[object_type] and list(tree[object_type].keys())

        objects[object_type]['children_types'] = children_types
        objects[object_type]['parent_type'] = parent_type

        if (not parent_type) and children_types:
            objects[object_type]['root_object'] = True

        if tree[object_type]:
            process_config_tree(objects, tree[object_type], object_type)
