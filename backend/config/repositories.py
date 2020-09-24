"""
    module de gestion de la configuarion des protocoles de suivi
"""

import os
from flask import current_app
from .utils import (
    customize_config,
    config_from_files,
    directory_last_modif,
    json_config_from_file,
    get_id_table_location,
    process_config_display,
    process_schema,
    CONFIG_PATH
)


# pour stocker la config dans current_app.config
config_cache_name = 'MONITORINGS_CONFIG'


def get_config_objects(module_path, config, tree=None, parent_type=None):
    '''
        recupere la config de chaque object present dans tree pour le module <module_path>
    '''
    if not tree:
        # initial tree
        tree = config['tree']

    for object_type in tree:

        # config object
        config[object_type] = config_object_from_files(module_path, object_type)

        # tree
        children_types = tree[object_type] and list(tree[object_type].keys())
        config[object_type]['children_types'] = children_types
        config[object_type]['parent_type'] = parent_type

        # schema
        process_schema(object_type, config)

        # display
        process_config_display(object_type, config)

        # root
        if (not parent_type) and children_types:
            config[object_type]['root_object'] = True

        # id_table_location
        config[object_type]['id_table_location'] = get_id_table_location(object_type)

        # recursif
        if tree[object_type]:
            get_config_objects(module_path, config, tree[object_type], object_type)


def config_object_from_files(module_path, object_type):
    '''
        recupere la configuration d'un object de type <object_type> pour le module <module_path>
    '''
    generic_config_object = json_config_from_file('generic', object_type)
    specific_config_object = {} if module_path == 'generic' else json_config_from_file(module_path, object_type)

    config_object = generic_config_object
    config_object.update(specific_config_object)

    return config_object


def get_config(module_path=None):
    '''
        recupere la configuration pour le module monitoring

        si la configuration en presente dans le dictionnaire current_app.config
        et si aucun fichier du dossier de configuration n'a été modifié depuis le dernier appel de cette fonction
            alors la configuration est récupéré depuis current_app.config
        sinon la config est recupérée depuis les fichiers du dossier de configuration et stockée dans current_app.config

    '''

    module_path = module_path if module_path else 'generic'

    module_confg_dir_path = CONFIG_PATH + '/' + module_path
    # test si le repertoire existe
    if not os.path.exists(module_confg_dir_path):
        return None

    # derniere modification
    last_modif = directory_last_modif(CONFIG_PATH)

    # test si present dans cache et pas modifée depuis le dernier appel
    config = current_app.config.get(config_cache_name, {}).get(module_path)

    if config and config.get('last_modif', 0) >= last_modif:
        return config

    print('config_get')

    config = config_from_files('config', module_path)
    get_config_objects(module_path, config)
    config['last_modif'] = last_modif

    # customize config
    customize_config(config, config_from_files('custom', module_path))

    # mise en cache dans current_app.config[config_cache_name][module_path]
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

    return config[object_type].get(param_name)


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
        return config[object_type][type_schema]

    # renvoie le schema complet si type_schema == 'all' ou par defaut
    schema = dict(config[object_type]['generic'])
    schema.update(config[object_type]['specific'])

    return schema


def get_config_frontend(module_path=None):

    config = dict(get_config(module_path))
    return config
