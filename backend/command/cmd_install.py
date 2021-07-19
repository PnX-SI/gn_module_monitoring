import os
import click

from flask.cli import AppGroup, with_appcontext
from sqlalchemy.sql import text

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_synthese.models import TSources

from ..monitoring.models import TMonitoringModules
from ..config.repositories import get_config
from ..config.utils import json_from_file, CONFIG_PATH
from ..modules.repositories import get_module, get_simple_module

from .utils import (
    process_img_modules,
    insert_permission_object,
    remove_monitoring_module,
    removesymlink,
    symlink,
    add_nomenclature
)

@click.command('process_img')
def cmd_process_img():
    '''
    Met à jour les images pour tout les modules
    '''
    process_img_modules()


@click.command('install')
@click.argument('module_config_dir_path')
@click.argument('module_code', type=str, required=False, default='')
@with_appcontext
def cmd_install_monitoring_module(module_config_dir_path, module_code):
    '''
        Module de suivi générique : installation d'un sous module

        Commande d'installation
        params :
            - module_config_dir_path (str) : chemin du répertoire
                    où se situe les fichiers de configuration du module
            - module_code (str): code du module (par defaut la dernière partie de module_config_dir_path )
    '''

    # on enleve le '/' de la fin de module_config_dir_path
    if module_config_dir_path[-1] == '/':
        module_config_dir_path = module_config_dir_path[:-1]

    module_code = module_code or module_config_dir_path.split('/')[-1]

    print('Install module {}'.format(module_code))

    module_monitoring = get_simple_module('module_code', 'MONITORINGS')

    try:
        module = get_simple_module('module_code', module_code)
        # test si le module existe
        if(module):
            print("Le module {} existe déjà".format(module_code))
            # TODO update??
            return
    except Exception:
        pass

    if not os.path.exists(module_config_dir_path):
        print(
            'module_config_dir_path {} does not exist (use absolute path)'.format(
                module_config_dir_path
            )
        )
        return

    # symlink to config dir
    symlink(module_config_dir_path, CONFIG_PATH + '/' + module_code)

    # process img modules
    process_img_modules()


    config = get_config(module_code)

    if not config:
        print(
            'config directory for module {} does not exist'.format(
                module_code
            )
        )
        return None

    module_desc = config['module'].get('module_desc')
    module_label = config['module'].get('module_label')
    synthese_object = config.get('synthese_object') or 'observation' # pour retrouver la page depuis la synthese

    if not(module_desc and module_label):
        print(
            "Veuillez renseigner les valeurs des champs module_label \
et module_desc dans le fichier <dir_module_suivi>/config/monitoring/module.json"
        )
        return

    module_data = {
        'module_code': module_code,
        'module_path': '{}/module/{}'.format(module_monitoring.module_path, module_code),
        'module_label': module_label,
        'module_desc': module_desc,
        'active_frontend': False,
        'active_backend': False,
        'module_picto': 'fa-puzzle-piece'
    }

    print('ajout du module {} en base'.format(module_code))
    module = TMonitoringModules()
    module.from_dict(module_data)
    DB.session.add(module)
    DB.session.commit()

    # Insert permission object
    if config['module'].get('permission_objects'):
        id_module = module.id_module
        insert_permission_object(id_module, config['module'].get('permission_objects'))

    #  run specific sql
    if os.path.exists(module_config_dir_path + '/synthese.sql'):
        print('Execution du script synthese.sql')
        sql_script = module_config_dir_path + '/synthese.sql'
        try:
            DB.engine.execute(
                text(
                    open(sql_script, 'r')
                    .read()
                    .replace(":'module_code'", "'{}'".format(module_code))
                    .replace(":module_code", "{}".format(module_code))
                ).execution_options(autocommit=True)
            )
        except Exception as e:
            print(e)
            print("Erreur dans le script synthese.sql")

    # insert nomenclature
    add_nomenclature(module_code)

    source_data= {
        'name_source': 'MONITORING_{}'.format(module_code.upper()),
        'desc_source': 'Données issues du module de suivi générique (sous-module: {})'.format(module_label.lower()),
        'entity_source_pk_field': 'gn_monitoring.vs_{}.entity_source_pk_value'.format(module_code.lower()),
        'url_source': '#/{}/object/{}/{}'.format(module_monitoring.module_path, module_code, synthese_object)
    }

    source = TSources(**source_data)
    DB.session.add(source)
    DB.session.commit()

    # TODO ++++ create specific tables

    return


@click.command('update_permission_objects')
@click.argument('module_code')
@with_appcontext
def cmd_update_perm_module_cmd(module_code):
    """
       Mise à jour (uniquement insertion) des objets permissions associés au module
       Défini par le paramètre permission_objects du fichier module.json

    Args:
        module_code ([string]): code du sous module

    """
    try:
        module = get_module('module_code', module_code)
    except Exception:
        print("le module n'existe pas")
        return
    path_module = CONFIG_PATH + '/' + module_code + '/module.json'

    if not os.path.exists(path_module):
        print(f"Il n'y a pas de fichier {path_module} pour ce module")
        return
    config_module = json_from_file(path_module, None)
    if not config_module:
        print('Il y a un problème avec le fichier {}'.format(path_module))
        return

    print(f"Insertion des objets de permissions pour le module {module_code}")
    # Insert permission object
    if "permission_objects" in config_module:
        id_module = module.id_module
        insert_permission_object(id_module, config_module["permission_objects"])
    else:
        print("no permission")



@click.command('remove')
@click.argument('module_code')
@with_appcontext
def cmd_remove_monitoring_module_cmd(module_code):
    '''
        Module de suivi générique : suppression d'un sous module

        Commande d'installation
        params :
            - module_code (str): code du module
    '''

    print('Remove module {}'.format(module_code))
    remove_monitoring_module(module_code)


@click.command('add_module_nomenclature')
@click.argument('module_code')
@with_appcontext
def cmd_add_module_nomenclature_cli(module_code):
    return add_nomenclature(module_code)


commands = [
    cmd_process_img,
    cmd_install_monitoring_module,
    cmd_update_perm_module_cmd,
    cmd_remove_monitoring_module_cmd,
    cmd_add_module_nomenclature_cli
]
