"""
    gestion des modules
    get_module
    get_modules
"""

from sqlalchemy.orm.exc import MultipleResultsFound

from geonature.utils.env import DB
from geonature.utils.errors import GeoNatureError

from ..models.monitoring import (
    TMonitoringModules,
)


def get_module(field_name, value):
    '''
    récupere un module de protocole de suivi a partir d'un paramètre

    le paramètre pour la recherche par défaut est 'id_module'
    on peut aussi utiliser 'module_code' ou 'module_path' selon les besoins

    :param value: Valeur du paramêtre
    :param field_name: Nom du champs utilisé pour la recherche
    :type value: int | str
    :type field_name: str, optional
    :return module as dict
    :rtype : dict

    '''

    if not hasattr(TMonitoringModules, field_name):
        raise GeoNatureError('get_module : TMonitoringModules ne possède pas de champs {}'.format(field_name))

    try:
        module = (
            DB.session.query(TMonitoringModules)
            .filter(
                getattr(TMonitoringModules, field_name) == value
            )
            .one()
        )

        return module

    except MultipleResultsFound:
        raise GeoNatureError(
            'get_module : multiple results found for field_name {} and value {}'
            .format(field_name, value)
        )
    except Exception as e:
        raise GeoNatureError(
            'get_module : {}'
            .format(str(e))
        )
        # dans ce case on renvoie None
        pass


def get_modules():
    '''
    récupère les modules de protocole de suivi
    renvoie un tableau de dictionnaires

    :return:
    '''

    modules_out = []

    try:
        res = (
            DB.session.query(TMonitoringModules)
            .all()
        )

        return res

    except Exception as e:
        raise GeoNatureError("MONITORINGS - get_modules : {}".format(str(e)))
        # en cas d'erreur on revoie []
        pass

    return modules_out
