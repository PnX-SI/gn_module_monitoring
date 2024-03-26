"""
    module de gestion de la configuarion des protocoles de suivi
"""

import os

from flask import current_app

from gn_module_monitoring.config.utils import (
    customize_config,
    config_from_files,
    json_config_from_file,
    get_id_table_location,
    process_config_display,
    process_schema,
    get_monitoring_module,
    get_monitorings_path,
    get_data_preload,
    monitoring_module_config_path,
)


# pour stocker la config dans current_app.config
config_cache_name = "MONITORINGS_CONFIG"


def get_config_objects(module_code, config, tree=None, parent_type=None, customSpecConfig=None):
    """
    recupere la config de chaque object present dans tree pour le module <module_code>
    """
    if not tree:
        # initial tree
        tree = config["tree"]

    if "module" in config["tree"]:
        is_sites_group_child = "sites_group" in list(dict.fromkeys(config["tree"]["module"]))

    for object_type in tree:
        # config object
        if not object_type in config:
            if object_type == "site":
                config[object_type] = config_object_from_files(
                    module_code, object_type, customSpecConfig, is_sites_group_child
                )
            else:
                config[object_type] = config_object_from_files(module_code, object_type)

        # tree
        children_types = tree[object_type] and list(tree[object_type].keys()) or []

        if not "children_types" in config[object_type]:
            config[object_type]["children_types"] = []
        config[object_type]["children_types"] += children_types
        config[object_type]["children_types"] = list(
            dict.fromkeys(config[object_type]["children_types"])
        )

        if not "parent_types" in config[object_type]:
            config[object_type]["parent_types"] = []

        if parent_type:
            config[object_type]["parent_types"].append(parent_type)
        config[object_type]["parent_types"] = list(
            dict.fromkeys(config[object_type]["parent_types"])
        )

        # config[object_type]['parent_type'] = parent_type

        # schema
        process_schema(object_type, config)

        # display
        process_config_display(object_type, config)

        # root
        if (not parent_type) and children_types:
            config[object_type]["root_object"] = True

        # id_table_location
        config[object_type]["id_table_location"] = get_id_table_location(object_type)

        # filters
        config[object_type]["filters"] = config[object_type].get("filters") or {}

        # recursif
        if tree[object_type]:
            get_config_objects(
                module_code, config, tree[object_type], object_type, customSpecConfig
            )


def config_object_from_files(module_code, object_type, custom=None, is_sites_group_child=False):
    """
    recupere la configuration d'un object de type <object_type> pour le module <module_code>
    """
    generic_config_object = json_config_from_file("generic", object_type)
    specific_config_object = (
        {"specific": {}}
        if module_code == "generic"
        else json_config_from_file(module_code, object_type)
    )

    # NOTE: Ici on pop la clé "id_sites_group" dans le cas ou l'entre par protocole car l'association de site à un groupe de site doit se faire par l'entrée par site
    if module_code != "generic" and object_type == "site" and not is_sites_group_child:
        generic_config_object["generic"].pop("id_sites_group")

    if module_code == "generic" and object_type == "site":
        generic_config_object["generic"]["types_site"] = {
            "type_widget": "datalist",
            "attribut_label": "Type(s) de site",
        }

    if object_type == "site" and custom is not None:
        if "specific" in custom and "specific" in specific_config_object:
            for key in custom["specific"]:
                if key not in specific_config_object["specific"]:
                    specific_config_object["specific"][key] = custom["specific"][key]

    config_object = generic_config_object
    config_object.update(specific_config_object)

    return config_object


def get_config_with_specific(module_code=None, force=False, complements=None):
    """
    recupere la configuration pour le module monitoring
    en prenant en compte les propriétés spécifiques des types de sites
    """
    customConfig = {"specific": {}}
    for keys in complements.keys():
        if "config" in complements[keys]:
            customConfig["specific"].update(
                (complements[keys].get("config", {}) or {}).get("specific", {})
            )
    get_config(module_code, force=True, customSpecConfig=customConfig)


def get_config(module_code=None, force=False, customSpecConfig=None):
    """
    recupere la configuration pour le module monitoring

    si la configuration en presente dans le dictionnaire current_app.config
    et si aucun fichier du dossier de configuration n'a été modifié depuis le dernier appel de cette fonction
        alors la configuration est récupéré depuis current_app.config
    sinon la config est recupérée depuis les fichiers du dossier de configuration et stockée dans current_app.config
    """
    module_code = module_code if module_code else "generic"

    module_confg_dir_path = monitoring_module_config_path(module_code)
    # test si le repertoire existe

    if module_code != "generic" and not os.path.exists(module_confg_dir_path):
        return None

    config = current_app.config.get(config_cache_name, {}).get(module_code)

    # pour ne pas verifier  a chaques fois
    #  explosion du nombre d'appels à la base sinon
    if config and not force:
        return config

    module = get_monitoring_module(module_code)
    # derniere modification
    # fichiers
    # file_last_modif = get_directory_last_modif(monitoring_config_path())
    # base_last_modif = get_base_last_modif(module)
    # last_modif = max(base_last_modif, file_last_modif)

    # test si present dans cache et pas modifée depuis le dernier appel

    # if config and config.get('last_modif', 0) >= last_modif:
    # return config

    config = config_from_files("config", module_code)
    get_config_objects(module_code, config, customSpecConfig=customSpecConfig)
    # customize config
    if module:
        config["custom"] = {}
        for field_name in [
            "module_code",
            "id_list_observer",
            "id_list_taxonomy",
            "b_synthese",
            "b_draw_sites_group",
            "taxonomy_display_field_name",
            "id_module",
        ]:
            var_name = "__MODULE.{}".format(field_name.upper())
            config["custom"][var_name] = getattr(module, field_name)
            config["module"][field_name] = getattr(module, field_name)

        # Types de sites
        if hasattr(module, field_name):
            config["module"]["types_site"] = [
                ts.id_nomenclature_type_site for ts in getattr(module, "types_site")
            ]

        config["custom"]["__MONITORINGS_PATH"] = get_monitorings_path()

        config["default_display_field_names"].update(config.get("display_field_names", {}))
        config["display_field_names"] = config["default_display_field_names"]

        # Remplacement des variables __MODULE.XXX
        #   par les valeurs spécifiées en base
        customize_config(config, config["custom"])

        # preload data # TODO auto from schemas && config recup tax users nomenclatures etc....
        config["data"] = get_data_preload(config, module)

    # mise en cache dans current_app.config[config_cache_name][module_code]
    if not current_app.config.get(config_cache_name, {}):
        current_app.config[config_cache_name] = {}
    current_app.config[config_cache_name][module_code] = config

    return config


def config_param(module_code, object_type, param_name):
    """
    revoie un parametre de la configuration des objets

    :param module_code: reference le module concerne
    :param object_type: le type d'object (site, visit, obervation)
    :param param_name: le parametre voulu (id_field_name, label)
    :type module_code: str
    :type object_type: str
    :type param_name: str
    :return: valeur du paramètre requis
    :rtype: str

    :Exemple:

    config_param('oedic', 'site', 'id_field_name')
        renverra 'id_base_site'

    config_param('oedic', 'site', 'label')
        renverra 'Site'

    """

    config = get_config(module_code)

    return config[object_type].get(param_name)


def config_schema(module_code, object_type, type_schema="all"):
    """
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

    :param module_code: reference le module concerne
    :param object_type: le type d'object (site, visit, obervation)
    :param type_schema: le type de schema requis ('all', 'generic', 'specific')
    :type module_code: str
    :type object_type: str
    :type type_schema: str, optional
    :return: tableau d'élément de configuration de formulaire
    :rtype: list
    """
    # recuperation de la configuration
    config = get_config(module_code)

    if type_schema in ["generic", "specific"]:
        return config[object_type][type_schema]

    # renvoie le schema complet si type_schema == 'all' ou par defaut
    schema = dict(config[object_type]["generic"])
    schema.update(config[object_type]["specific"])

    return schema


def get_config_frontend(module_code=None, force=True):
    config = dict(get_config(module_code, force))
    return config


# def get_config_from_backend(module_code=None, force=False):

#     module_code = 'generic'
#     #TODO: voir la sortie de cette fonction
#     config = config_from_backend('config', module_code)
#     #TODO: voir également à quoi sert cette fonction
#     get_config_objects(module_code, config)
