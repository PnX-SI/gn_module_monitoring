"""
    module de gestion de la configuarion des protocoles de suivi
"""

import os
from flask import current_app
from ..modules.repositories import get_module
from .data_utils import get_data_utils
from .utils import (
    copy_dict,
    customize_config,
    config_from_files,
    directory_last_modif,
    json_config_from_file,
    json_schema_from_file,
    keys_remove_doublons,
    process_config_display,
    process_config_tree,
    process_schema,
    schema_dict_to_array
)

# chemin ver le repertoire de la config
config_path = os.path.dirname(os.path.abspath(
    __file__)) + '/../../config/monitoring'

# pour stocker la config dans current_app.config
config_cache_name = 'MONITORINGS_CONFIG'


def config_objects_from_files(module_path):

    generic_config_objects = json_config_from_file('generic', 'objects')
    specific_config_objects = {} if module_path == 'generic' else json_config_from_file(module_path, 'objects')

    object_types = keys_remove_doublons(
        generic_config_objects,
        specific_config_objects
    )

    config_objects = {}
    for object_type in object_types:

        config_object = generic_config_objects.get(object_type, {})
        config_object.update(specific_config_objects.get(object_type, {}))
        config_objects[object_type] = config_object

    # cas ou inherit_type dans config
    # dans ce cas l'object prend les caracteristiques genrerique de inherit_type
    for object_type in object_types:

        inherit_type = config_objects[object_type].get('inherit_type')
        if not inherit_type:
            continue
        config_object = copy_dict(config_objects[object_type])
        generic_config_inherit = config_objects_from_files('generic').get(inherit_type)
        generic_config_inherit.update(config_object)
        config_objects[object_type] = generic_config_inherit

    return config_objects


def schema_from_file(module_path, object_type):
    generic_schema_object = json_schema_from_file('generic', object_type)
    specific_schema_object = {} if module_path == 'generic' else json_schema_from_file(module_path, object_type)

    process_schema(generic_schema_object, specific_schema_object)

    return {
        'generic': generic_schema_object,
        'specific': specific_schema_object
    }

    return generic_schema_object


def inherit_schema(module_path, object_type, schemas, config_objects):
    inherit_type = config_objects[object_type].get('inherit_type')
    if not inherit_type:
        return schemas[object_type]

    schema_inherit = {
        'generic': json_schema_from_file('generic', inherit_type),
        'specific': {}
    }

    schema_object = schemas[object_type]
    schema_object['generic'].update(schema_object['specific'])
    all_schema_object = schema_object['generic']

    process_schema(schema_inherit['generic'], all_schema_object)
    process_schema(schema_inherit['specific'], all_schema_object)
    schema_inherit['specific'].update(all_schema_object)

    schema_object = copy_dict(schema_inherit)

    return schema_object


def schemas_from_files(module_path):

    schemas = {}

    config_objects = config_objects_from_files(module_path)
    object_types = list(config_objects.keys())
    object_types.remove('tree')

    for object_type in object_types:

        schemas[object_type] = schema_from_file(module_path, object_type)

    # heritage
    for object_type in object_types:

        schemas[object_type] = inherit_schema(module_path, object_type, schemas, config_objects)

    # passage de dict à array
    for object_type in object_types:
        for type_schema in ['generic', 'specific']:
            schemas[object_type][type_schema] = schema_dict_to_array(
                schemas[object_type][type_schema])

    return schemas


def get_config(module_path=None):
    '''
        recupere la configuration pour le module monitoring

        si la configuration en presente dans le dictionnaire current_app.config
        et si aucun fichier du dossier de configuration n'a été modifié depuis le dernier appel de cette fonction
            alors la configuration est récupéré depuis current_app.config
        sinon la config est recupérée depuis les fichiers du dossier de configuration et stockée dans current_app.config

    '''

    module_path = module_path if module_path else 'generic'

    # derniere modification
    last_modif = directory_last_modif(config_path)

    # test si present dans cache et pas modifée depuis le dernier appel
    config = current_app.config.get(config_cache_name, {}).get(module_path)

    if config and config.get('last_modif', 0) >= last_modif:
        return config

    print('config_get')

    try:
        module = get_module('module_path', module_path)
    except Exception:
        module = None

    if module_path != 'generic' and not module:
        module_path = 'generic'
        # return []  # TODO exception

    config = {
        'data': config_from_files('data', module_path),
        'schemas': schemas_from_files(module_path),
        'objects': config_objects_from_files(module_path),
        'last_modif': last_modif
    }

    # tree : definit les parent_type et children types
    process_config_tree(config['objects'])

    # patch display et properties keys
    process_config_display(config)

    # customize_config
    customize_config(config, config_from_files('custom', module_path))

    # mise en cache
    if not current_app.config.get(config_cache_name, {}):
        current_app.config[config_cache_name] = {}
    current_app.config[config_cache_name][module_path] = config

    return config


def config_param(module_path, object_type, param_name):
    '''
        revoie un parametre de la configuration des objets

        :param module_path: reference le module concerne
        :param object_type: le type d'object (site, visit, obervation)
        :param param_name: le parametre voulu (id_field_name, label)
        :type module_path: str
        :type object_type: str
        :type param_name: str
        :return: valeur du paramètre requis
        :rtype: str

        :Exemple:

        config_param('oedic', 'site', 'id_field_name')
            renverra 'id_base_site'

        config_param('oedic', 'site', 'label')
            renverra 'Site'

    '''

    config = get_config(module_path)

    return config['objects'][object_type].get(param_name)


def config_schema(module_path, object_type, type_schema="all"):
    '''
        renvoie une liste d'éléments de configuration de formulaire

        pour type_schema:
            'generic' : renvoie le schema générique
            'specific' : renvoie le schema spécifique
            'all': par defaut renvoie tout le schema

        Un élément est un dictionaire de type
            {
                "attribut_name": "id_base_site",
                "Label": "Id du site",
                "type_widget": "integer",
                "required": "true",
            }

        :param module_path: reference le module concerne
        :param object_type: le type d'object (site, visit, obervation)
        :param type_schema: le type de schema requis ('all', 'generic', 'specific')
        :type module_path: str
        :type object_type: str
        :type type_schema: str, optional
        :return: tableau d'élément de configuration de formulaire
        :rtype: list
    '''
    # recuperation de la configuration
    config = get_config(module_path)

    if type_schema in ["generic", "specific"]:
        return config['schemas'][object_type][type_schema]

    # renvoie le schema complet si type_schema=='all' ou par defaut
    return config['schemas'][object_type]['generic'] + config['schemas'][object_type]['specific']


def get_config_frontend(module_path=None):

    config = dict(get_config(module_path))
    # config.pop('data_utils')
    return config
