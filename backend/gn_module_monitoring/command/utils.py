import os
from pathlib import Path
from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_permissions.models import TObjects

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..config.utils import (
    json_from_file,
    monitoring_module_config_path,
    SUB_MODULE_CONFIG_DIR
)

from ..modules.repositories import get_module, get_source_by_code, get_modules


'''
utils.py

fonctions pour les commandes du module monitoring
'''

def process_for_all_module(process_func):
    '''
        boucle sur les répertoire des module
            et exécute la fonction <process_func> pour chacun
            (sauf generic)
    '''
    for module in get_modules():
        process_func(module.module_code)
    return



def process_export_csv(module_code=None):
    '''
        fonction qui va chercher les fichier sql de exports/csv et qui les joue
    '''

    if not module_code:
        '''
            pour tous les modules
        '''
        return process_for_all_module(process_export_csv)

    export_csv_dir = Path(monitoring_module_config_path(module_code)) / 'exports/csv'

    if not export_csv_dir.is_dir():
        return

    for root, dirs, files in os.walk(export_csv_dir, followlinks=True):
        for f in files:
            if not f.endswith('.sql'):
                continue

            try:
                DB.engine.execute(
                    text(
                        open(Path(root) / f, 'r')
                        .read()
                    ).execution_options(autocommit=True)
                    .bindparams(module_code=module_code)
                )
                print('{} - export csv file : {}'.format(module_code, f))

            except Exception as e:
                print('{} - export csv erreur dans le script {} : {}'.format(module_code, f ,e))


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

def add_nomenclature(module_code):
    path_nomenclature = monitoring_module_config_path(module_code) / 'nomenclature.json'

    if not path_nomenclature.is_file():
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

def installed_modules():
    return [ module.module_code for module in get_modules()]

def available_modules():
    '''
        renvoie la liste des modules disponibles non encore installés
    '''
    installed_modules_ = installed_modules()
    for root, dirs, files in os.walk(SUB_MODULE_CONFIG_DIR, followlinks=True):
        return [ str(d) for d in dirs if d not in installed_modules_ ]