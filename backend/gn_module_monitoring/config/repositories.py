"""
    module de gestion de la configuarion des protocoles de suivi
"""

import os

from flask import current_app

from gn_module_monitoring.config.utils import (
    customize_config,
    config_from_files,
    json_config_from_db,
    json_config_from_file,
    get_id_table_location,
    process_config_display,
    process_schema,
    get_monitoring_module,
    get_monitorings_path,
    get_data_preload,
    monitoring_module_config_path,
)
from gn_module_monitoring.utils.utils import dict_deep_update

# pour stocker la config dans current_app.config
config_cache_name = "MONITORINGS_CONFIG"


def get_config_objects(module_code, config, tree=None, parent_type=None):
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
                    module_code, object_type, is_sites_group_child
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
            get_config_objects(module_code, config, tree[object_type], object_type)


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
    db_config_object = {"specific": {}}

    if object_type == "site":
        db_config_object = json_config_from_db(module_code)
        # Mise a jour des configurations de façon récursive
        dict_deep_update(
            specific_config_object.get("specific", {}), db_config_object.get("specific", {})
        )
    elif object_type == "module":
        db_config_object = json_config_from_db(module_code)
        specific_config_object["types_site"] = db_config_object["types_site"]
        db_config_object = {"specific": {}}

    if module_code == "generic" and object_type == "site":
        generic_config_object["generic"]["types_site"] = {
            "type_widget": "datalist",
            "attribut_label": "Type(s) de site",
            "type_util": "types_site",
            "keyValue": "id_nomenclature_type_site",
            "keyLabel": "label",
            "multiple": True,
            "api": "monitorings/modules/generic/types_sites",
            "application": "GeoNature",
            "required": True,
            "nullDefault": True,
            "designStyle": "bootstrap",
            "definition": "Permet de n'avoir que les types de site lié au module",
        }
        specific_config_object["specific"]["id_sites_group"] = {"required": False, "hidden": False}

    # if object_type == "site" and custom is not None:
    #     if "specific" in custom and "specific" in specific_config_object:
    #         for key in custom["specific"]:
    #             if key not in specific_config_object["specific"]:
    #                 specific_config_object["specific"][key] = custom["specific"][key]

    config_object = generic_config_object
    config_object.update(db_config_object)
    config_object.update(specific_config_object)
    return config_object


def get_config(module_code=None, force=False):
    """
    recupere la configuration pour le module monitoring

    si la configuration en presente dans le dictionnaire current_app.config
    et si aucun fichier du dossier de configuration n'a été modifié depuis le dernier appel de cette fonction
        alors la configuration est récupéré depuis current_app.config
    sinon la config est recupérée depuis les fichiers du dossier de configuration et stockée dans current_app.config
    """
    if module_code == "MONITORINGS":
        module_code = "generic"
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
    get_config_objects(module_code, config)

    # customize config
    config["custom"] = {}
    if module:
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

            config["custom"]["__MODULE.TYPES_SITE"] = [
                type_site.as_dict() for type_site in module.types_site
            ]
            config["custom"]["__MODULE.IDS_TYPE_SITE"] = [
                {"id_nomenclature_type_site": t.id_nomenclature_type_site}
                for t in module.types_site
            ]
            config["default_display_field_names"].update(config.get("display_field_names", {}))
            config["display_field_names"] = config["default_display_field_names"]

            # preload data # TODO auto from schemas && config recup tax users nomenclatures etc....
            config["data"] = get_data_preload(config, module)
    else:
        # Si module est généric
        config["custom"]["CODE_OBSERVERS_LIST"] = current_app.config["MONITORINGS"].get(
            "CODE_OBSERVERS_LIST", {}
        )
        config["custom"]["__MODULE.MODULE_CODE"] = "generic"
        config["custom"]["__MODULE.ID_MODULE"] = None
        config["custom"]["__MODULE.B_SYNTHESE"] = False

    config["custom"]["__MONITORINGS_PATH"] = get_monitorings_path()
    # Remplacement des variables __MODULE.XXX
    #   par les valeurs spécifiées en base
    customize_config(config, config["custom"])

    # mise en cache dans current_app.config[config_cache_name][module_code]
    if not current_app.config.get(config_cache_name, {}):
        current_app.config[config_cache_name] = {}
    current_app.config[config_cache_name][module_code] = config

    return config


# def get_config_from_backend(module_code=None, force=False):

#     module_code = 'generic'
#     #TODO: voir la sortie de cette fonction
#     config = config_from_backend('config', module_code)
#     #TODO: voir également à quoi sert cette fonction
#     get_config_objects(module_code, config)
