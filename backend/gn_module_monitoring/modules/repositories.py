"""
    gestion des modules
    get_module
    get_modules
"""

from sqlalchemy.orm import Load
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy import select

from geonature.utils.env import DB
from geonature.utils.errors import GeoNatureError

from geonature.core.gn_commons.models import TModules
from geonature.core.gn_synthese.models import TSources
from ..monitoring.models import TMonitoringModules


def get_simple_module(field_name, value):
    """
    récupere un module a partir d'un paramètre

    le paramètre pour la recherche par défaut est 'id_module'
    on peut aussi utiliser 'module_code' selon les besoins

    :param value: Valeur du paramêtre
    :param field_name: Nom du champs utilisé pour la recherche
    :type value: int | str
    :type field_name: str, optional
    :return module as dict
    :rtype : dict

    """
    return get_module(field_name, value, TModules)


def get_module(field_name, value, moduleCls=TMonitoringModules):
    """
    récupere un module de protocole de suivi a partir d'un paramètre

    le paramètre pour la recherche par défaut est 'id_module'
    on peut aussi utiliser 'module_code' selon les besoins

    :param value: Valeur du paramêtre
    :param field_name: Nom du champs utilisé pour la recherche
    :type value: int | str
    :type field_name: str, optional
    :return module as dict
    :rtype : dict

    """

    if not hasattr(moduleCls, field_name):
        raise GeoNatureError(
            "get_module : TMonitoringModules ne possède pas de champs {}".format(field_name)
        )

    try:
        module = DB.session.execute(
            select(moduleCls).where(getattr(moduleCls, field_name) == value)
        ).scalar_one()

        return module

    except MultipleResultsFound:
        raise GeoNatureError(
            "get_module : multiple results found for field_name {} and value {}".format(
                field_name, value
            )
        )
    except Exception as e:
        raise GeoNatureError("get_module : {}".format(str(e)))
        # dans ce case on renvoie None
        pass


def get_modules(session=None):
    """
    récupère les modules de protocole de suivi
    renvoie un tableau de dictionnaires

    :return:
    """

    if not session:
        session = DB.session
    try:
        res = session.scalars(
            select(TMonitoringModules).order_by(TMonitoringModules.module_label)
        ).all()

        return res

    except Exception as e:
        raise GeoNatureError("MONITORINGS - get_modules : {}".format(str(e)))
        # en cas d'erreur on revoie []


def get_source_by_code(value):
    try:
        source = DB.session.execute(
            select(TSources).where(TSources.name_source == value)
        ).scalar_one()

        return source

    except MultipleResultsFound:
        raise GeoNatureError("get_source : multiple results found for  {}".format(value))
    except NoResultFound:
        raise GeoNatureError("get_source : no results found for  {}".format(value))
    except Exception as e:
        raise GeoNatureError("get_source : {}".format(str(e)))
        # dans ce case on renvoie None
        pass
