import os
from pathlib import Path
from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_permissions.models import TObjects

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from ..config.utils import json_from_file, MONITORING_CONFIG_PATH

from ..modules.repositories import get_module, get_source_by_code


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
    for root, dirs, files in os.walk(Path(MONITORING_CONFIG_PATH), followlinks=True):
        for d in dirs:
            if d == 'generic':
                continue
            process_func(d)
        break # walk depth = 1
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

    export_csv_dir = Path(MONITORING_CONFIG_PATH) / module_code / 'exports/csv'

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


def process_export_pdf(module_code=None):
    '''
        fonction qui place les fichiers pour les exports pdf

        template dans le dossier :
        images, css dans le dossier : static/external_assets/monitorings/<module_code.lower()>/exports/pdf/
    '''


    if not module_code:
        '''
            pour tous les modules
        '''
        return process_for_all_module(process_export_pdf)

    # static (css img etc.)

    export_pdf_assets_static_dir = BACKEND_DIR / 'static/external_assets/monitorings/{}/exports/pdf'.format(module_code)
    export_pdf_assets_static_dir.parent.mkdir(exist_ok=True, parents=True)

    export_pdf_dir = Path(MONITORING_CONFIG_PATH) / module_code / 'exports/pdf'

    if not export_pdf_dir.is_dir():
        return

    symlink(
        export_pdf_dir,
        export_pdf_assets_static_dir
    )


    # template html

    template_dir = BACKEND_DIR / 'geonature/templates/modules/monitorings/{}'.format(module_code)
    template_dir.mkdir(exist_ok=True, parents=True)

    for root, dirs, files in os.walk(export_pdf_dir, followlinks=True):
        for f in files:
            if not  f.endswith('.html'):
                continue
            print('{} - export pdf template : {}'.format(module_code, f))
            symlink(
                Path(root) / f,
                template_dir / f
            )




def process_img_modules():
    '''
    function qui met à jour toutes les images pour les modules
    '''

    # creation du fichier d'asset dans le repertoire static du backend
    assets_static_dir = BACKEND_DIR / 'static/external_assets/monitorings/'
    assets_static_dir.mkdir(exist_ok=True, parents=True)

    for root, dirs, files in os.walk(MONITORING_CONFIG_PATH, followlinks=True):
        img_file = root / Path('img.jpg', )
        if not img_file.is_file():
            continue

        module_code = str(img_file).split('/')[-2].lower()

        symlink(
            img_file,
            assets_static_dir / Path(module_code + '.jpg')
        )


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

    # remove symlink config
    if os.path.exists(MONITORING_CONFIG_PATH + '/' + module_code):
        removesymlink(MONITORING_CONFIG_PATH + '/' + module_code)

    # remove symlink image menu modules de suivi
    img_link = MONITORING_CONFIG_PATH + '/../../frontend/assets/' + module_code + '.jpg'
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
        os.remove(path)


def symlink(path_source, path_dest):
    if(os.path.islink(path_dest)):
        os.remove(path_dest)
    os.symlink(path_source, path_dest)


def add_nomenclature(module_code):
    path_nomenclature = MONITORING_CONFIG_PATH + '/' + module_code + '/nomenclature.json'

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
