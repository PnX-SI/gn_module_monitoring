import os
import click
from flask import Flask
from flask.cli import AppGroup, with_appcontext
from sqlalchemy import and_

from geonature.utils.env import DB
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..models.monitoring import TMonitoringModules
from ..config.repositories import config_param, get_config
from ..config.utils import json_from_file, CONFIG_PATH
from ..modules.repositories import get_module

app = Flask(__name__)
monitorings_cli = AppGroup('monitorings')


@monitorings_cli.command('install')
@click.argument('module_config_dir_path')
@click.argument('module_path')
@with_appcontext
def install_monitoring_module(module_config_dir_path, module_path):
    '''
        Module de suivi générique : installation d'un sous module

        Commande d'inst
    '''

    print('Install module {}'.format(module_path))

    try:
        module = get_module('module_path', module_path)
        # test si le module existe
        if(module):
            print("Le module {} existe déjà".format(module_path))
            # TODO update??
            return
    except Exception:
        pass

    if not os.path.exists(module_config_dir_path):
        print('module_config_dir_path_does not exist (use absolute path)'.format(module_config_dir_path))
        return

    # symlink to config dir
    symlink(module_config_dir_path, CONFIG_PATH + '/' + module_path)

    # symlink image menu modules de suivi
    if os.path.exists(module_config_dir_path + '/img.jpg'):
        symlink(
            module_config_dir_path + '/img.jpg',
            CONFIG_PATH + '/../../frontend/assets/' + module_path + '.jpg'
        )

    if not get_config(module_path):
        print('config directotry for module {} does not exist'.format(module_path))
        return None

    module_desc = config_param(module_path, 'module', 'module_desc')
    module_label = config_param(module_path, 'module', 'module_label')

    if not(module_desc and module_label):
        print(
            "Veuillez renseigner les valeurs des champs module_label \
et module_desc dans le fichier <dir_module_suivi>/config/monitoring/module.json"
        )
        return

    module_data = {
        'module_path': module_path,
        'module_code': module_path,
        'module_label': module_label,
        'module_desc': module_desc,
        'active_frontend': False,
        'active_backend': False
    }

    print('ajout du module {} en base'.format(module_path))
    module = TMonitoringModules()
    module.from_dict(module_data)
    DB.session.add(module)
    DB.session.commit()

    # TODO insert nomenclature
    add_nomenclature(module_path)

    # TODO ++++ create specific tables

    return


def symlink(path_source, path_dest):
    if(os.path.islink(path_dest)):
        print('remove link ' + path_dest)
        os.remove(path_dest)
    os.symlink(path_source, path_dest)


@monitorings_cli.command('add_module_nomenclature')
@click.argument('module_path')
@with_appcontext
def add_module_nomenclature_cli(module_path):
    return add_nomenclature(module_path)


def add_nomenclature(module_path):
    path_nomenclature = CONFIG_PATH + '/' + module_path + '/nomenclature.json'

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
            print('no insert nomenclature', nomenclature_type)
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
            print('probleme de type avec mnemonique="{}" pour la nomenclature'.format(data['type'], data))
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
