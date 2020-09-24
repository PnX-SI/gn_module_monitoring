import os
import click
from pathlib import Path

import subprocess


from flask import Flask
from flask.cli import AppGroup, with_appcontext
from sqlalchemy import and_
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError

from geonature.utils.env import DB
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..models.monitoring import TMonitoringModules
from ..config.repositories import config_param, get_config
from ..config.utils import json_from_file, CONFIG_PATH
from ..modules.repositories import get_module, get_simple_module, get_source_by_code

app = Flask(__name__)
monitorings_cli = AppGroup('monitorings')


@monitorings_cli.command('install')
@click.argument('module_config_dir_path')
@click.argument('module_path')
@click.option("--build", type=bool, required=False, default=True)
@with_appcontext
def install_monitoring_module(module_config_dir_path, module_path, build):
    '''
        Module de suivi générique : installation d'un sous module

        Commande d'installation
        params :
            - module_config_dir_path (str) : chemin du répertoire
                    où se situe les fichiers de configuration du module
            - module_path (str): code du module
    '''

    print('Install module {}'.format(module_path))

    module_monitoring = get_simple_module('module_code', 'MONITORINGS')

    try:
        module = get_simple_module('module_path', module_path)
        # test si le module existe
        if(module):
            print("Le module {} existe déjà".format(module_path))
            # TODO update??
            return
    except Exception:
        pass

    if not os.path.exists(module_config_dir_path):
        print(
            'module_config_dir_path_does not exist (use absolute path)'.format(
                module_config_dir_path
            )
        )
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
        print(
            'config directory for module {} does not exist'.format(
                module_path
            )
        )
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
        'module_code': module_path, # ??? Pourquoi module_code = module_path
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

    #  run specific sql
    if os.path.exists(module_config_dir_path + '/synthese.sql'):
        print('Execution du script synthese.sql')
        sql_script = module_config_dir_path + '/synthese.sql'
        try:
            DB.engine.execute(
                text(
                    open(sql_script, 'r').read()
                ).execution_options(autocommit=True)
            )
        except Exception as e:
            print(e)
            print("Erreur dans le script synthese.sql")

    # insert nomenclature
    add_nomenclature(module_path)

    # creation source pour la synthese
    txt = ("""
    INSERT INTO gn_synthese.t_sources(
        name_source,
        desc_source,
        entity_source_pk_field,
        url_source
    )
    VALUES (
        'MONITORING_{0}',
        'Données issues du module de suivi générique (sous-module: {1})',
        'gn_monitoring.vs_{2}.entity_source_pk_value',
        '#/{3}/object/{2}/visit/observation'
    );
        """.format(
            module_path.upper(), # MONITORING_TEST
            module_label.lower(), # module de test
            module.module_path, # test
            module_monitoring.module_path, # monitorings
        )
    )

    DB.engine.execution_options(autocommit=True).execute(txt)

    # exec geonature (update img)
    if build:
        subprocess.call(
            [
                "geonature update_module_configuration {}"
                .format(module_monitoring.module_code)
            ],
            shell=True)

    # TODO ++++ create specific tables

    return


@monitorings_cli.command('remove')
@click.argument('module_path')
@with_appcontext
def remove_monitoring_module_cmd(module_path):
    '''
        Module de suivi générique : suppression d'un sous module

        Commande d'installation
        params :
            - module_path (str): code du module
    '''

    print('Remove module {}'.format(module_path))
    remove_monitoring_module(module_path)


def remove_monitoring_module(module_path):
    try:
        module = get_module('module_path', module_path)
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
    except IntegrityError as ie:
        print("Impossible de supprimer le module car il y a des données associées")
        return
    except Exception as e:
        print("Impossible de supprimer le module")
        raise(e)

    # remove symlink config
    if os.path.exists(CONFIG_PATH + '/' + module_path):
        removesymlink(CONFIG_PATH + '/' + module_path)

    # remove symlink image menu modules de suivi
    img_link = CONFIG_PATH + '/../../frontend/assets/' + module_path + '.jpg'
    if os.path.exists(img_link):
        removesymlink(img_link)

    # suppression source pour la synthese
    try:
        print('Remove source {}'.format("MONITORING_" + module_path.upper()))
        source = get_source_by_code("MONITORING_" + module_path.upper())
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
