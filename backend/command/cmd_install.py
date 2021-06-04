import os
import click
from pathlib import Path

import subprocess


from flask import Flask
from flask.cli import AppGroup, with_appcontext
from sqlalchemy import and_
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from geonature.utils.env import DB
from geonature.core.gn_permissions.models import TObjects
from geonature.core.gn_synthese.models import TSources

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..monitoring.models import TMonitoringModules
from ..config.repositories import config_param, get_config
from ..config.utils import json_from_file, CONFIG_PATH
from ..modules.repositories import get_module, get_simple_module, get_source_by_code

app = Flask(__name__)
monitorings_cli = AppGroup('monitorings')


@monitorings_cli.command('install')
@click.argument('module_config_dir_path')
@click.argument('module_code', type=str, required=False, default='')
@click.option("--build", type=bool, required=False, default=True)
@with_appcontext
def install_monitoring_module(module_config_dir_path, module_code, build):
    '''
        Module de suivi générique : installation d'un sous module

        Commande d'installation
        params :
            - module_config_dir_path (str) : chemin du répertoire
                    où se situe les fichiers de configuration du module
            - module_code (str): code du module (par defaut la dernière partie de module_config_dir_path )
            - build: si on relance un build du frontend après l'installation du sous-module
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

    # symlink image menu modules de suivi
    if os.path.exists(module_config_dir_path + '/img.jpg'):
        symlink(
            module_config_dir_path + '/img.jpg',
            CONFIG_PATH + '/../../frontend/assets/' + module_code + '.jpg'
        )

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

    # exec geonature (update img)
    if build:
        subprocess.call(
            [
                "geonature frontend_build"
            ],
            shell=True)

    # TODO ++++ create specific tables

    return


def insert_permission_object(id_module, permissions):
    """ Insertion de l'association permission object

        Args:
            id_module ([type]): id du module
            permissions ([type]): liste des permissions à associer au module

        Raises:
            e: [description]
    """
    for perm in permissions:
        print(f"Insert perm {perm}")
        # load object
        try:
            object = DB.session.query(TObjects).filter(TObjects.code_object == perm).one()
            # save
            txt = ("""
                    INSERT INTO gn_permissions.cor_object_module (id_module, id_object)
                    VALUES ({id_module}, {id_object})
                """.format(
                    id_module=id_module,
                    id_object=object.id_object
                )
            )
            try:
                DB.engine.execution_options(autocommit=True).execute(txt)
                print(f"    Ok")
            except IntegrityError:
                DB.session.rollback()
                print(f"    Impossible d'insérer la permission {perm} pour des raisons d'intégrités")
        except NoResultFound as e:
            print(f"    Permission {perm} does'nt exists")
        except Exception as e:
            print(f"    Impossible d'insérer la permission {perm} :{e}")



@monitorings_cli.command('update_permission_objects')
@click.argument('module_code')
@with_appcontext
def update_perm_module_cmd(module_code):
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



@monitorings_cli.command('remove')
@click.argument('module_code')
@with_appcontext
def remove_monitoring_module_cmd(module_code):
    '''
        Module de suivi générique : suppression d'un sous module

        Commande d'installation
        params :
            - module_code (str): code du module
    '''

    print('Remove module {}'.format(module_code))
    remove_monitoring_module(module_code)


def remove_monitoring_module(module_code):
    try:
        module = get_module('module_code', module_code)
    except Exception:
        print("le module n'existe pas")
        return

    # remove module in db
    try:
        # HACK pour le moment suprresion avec un sql direct
        #  Car il y a un soucis de delete cascade dans les modèles sqlalchemy
        txt = ("""
                    DELETE FROM gn_commons.t_modules WHERE id_module ={}
                """.format(
                    module.id_module
                )
        )

        DB.engine.execution_options(autocommit=True).execute(txt)
    except IntegrityError:
        print("Impossible de supprimer le module car il y a des données associées")
        return
    except Exception:
        print("Impossible de supprimer le module")
        raise(e)

    # remove symlink config
    if os.path.exists(CONFIG_PATH + '/' + module_code):
        removesymlink(CONFIG_PATH + '/' + module_code)

    # remove symlink image menu modules de suivi
    img_link = CONFIG_PATH + '/../../frontend/assets/' + module_code + '.jpg'
    if os.path.exists(img_link):
        removesymlink(img_link)

    # suppression source pour la synthese
    try:
        print('Remove source {}'.format("MONITORING_" + module_code.upper()))
        source = get_source_by_code("MONITORING_" + module_code.upper())
        DB.session.delete(source)
        DB.session.commit()
    except Exception as e:
        print("Impossible de supprimer la source {}".format(str(e)))
        return
    # run specific sql TODO
    # remove nomenclature TODO
    return


def removesymlink(path):
    if(os.path.islink(path)):
        print('remove link ' + path)
        os.remove(path)


def symlink(path_source, path_dest):
    if(os.path.islink(path_dest)):
        print('remove link ' + path_dest)
        os.remove(path_dest)
    os.symlink(path_source, path_dest)


@monitorings_cli.command('add_module_nomenclature')
@click.argument('module_code')
@with_appcontext
def add_module_nomenclature_cli(module_code):
    return add_nomenclature(module_code)


def add_nomenclature(module_code):
    path_nomenclature = CONFIG_PATH + '/' + module_code + '/nomenclature.json'

    if not os.path.exists(path_nomenclature):
        print("Il n'y a pas de nomenclature à insérer pour ce module")
        return

    nomenclature = json_from_file(path_nomenclature, None)
    if not nomenclature:
        print('Il y a un problème avec le fichier {}'.format(path_nomenclature))
        return

    for data in nomenclature.get('types', []):
        nomenclature_type = None
        try:
            nomenclature_type = (
                DB.session.query(BibNomenclaturesTypes)
                .filter(
                    data.get('mnemonique') == BibNomenclaturesTypes.mnemonique
                )
                .one()
            )

        except Exception:
            pass

        if nomenclature_type:
            print('no insert type', nomenclature_type)
            continue

        data['label_fr'] = data.get('label_fr') or data['label_default']
        data['definition_fr'] = data.get('definition_fr') or data['definition_default']
        data['source'] = data.get('source') or 'monitoring'
        data['statut'] = data.get('statut') or 'Validation en cours'

        nomenclature_type = BibNomenclaturesTypes(**data)
        DB.session.add(nomenclature_type)
        DB.session.commit()

    for data in nomenclature['nomenclatures']:
        nomenclature = None
        try:
            nomenclature = (
                DB.session.query(TNomenclatures)
                .join(
                    BibNomenclaturesTypes,
                    BibNomenclaturesTypes.id_type == TNomenclatures.id_type
                )
                .filter(
                    and_(
                        data.get('cd_nomenclature') == TNomenclatures.cd_nomenclature,
                        data.get('type') == BibNomenclaturesTypes.mnemonique
                    )
                )
                .one()
            )

        except Exception as e:
            pass

        if nomenclature:
            # TODO make update
            print(
                'nomenclature {} - {} already exist'.format(
                    nomenclature.cd_nomenclature,
                    nomenclature.label_default
                )
            )
            continue

        id_type = None

        try:
            id_type = (
                DB.session.query(BibNomenclaturesTypes.id_type)
                .filter(
                    BibNomenclaturesTypes.mnemonique == data['type']
                )
                .one()
            )[0]
        except Exception:
            pass

        if not id_type:
            print('probleme de type avec mnemonique="{}" pour la nomenclature {}'.format(data['type'], data))
            continue

        data['label_fr'] = data.get('label_fr') or data['label_default']
        data['definition_fr'] = data.get('definition_fr') or data['definition_default']
        data['source'] = data.get('source') or 'monitoring'
        data['statut'] = data.get('statut') or 'Validation en cours'
        data['active'] = True
        data['id_type'] = id_type
        data.pop('type')

        nomenclature = TNomenclatures(**data)
        DB.session.add(nomenclature)
        DB.session.commit()
