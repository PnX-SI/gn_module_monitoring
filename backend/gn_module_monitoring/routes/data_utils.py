"""
Routes pour récupérer des paramètre
    d'utilisateurs
    de nomenclature
    de taxonomie

    TODO cache
"""

from flask import request

from sqlalchemy import and_, inspect, cast, select
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from geonature.utils.env import DB
from geonature.core.users.models import VUserslistForallMenu
from geonature.core.gn_meta.models import TDatasets
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.gn_commons.models import TModules

from pypnusershub.db.models import User, UserList

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from pypnnomenclature.repository import get_nomenclature_list

from apptax.taxonomie.models import Taxref, BibListes

from utils_flask_sqla.response import json_resp

from pypn_habref_api.models import Habref

from ref_geo.models import LAreas, LiMunicipalities

from gn_module_monitoring.blueprint import blueprint
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.utils.routes import get_sites_groups_from_module_id
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema
from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringSitesGroups,
)

model_dict = {
    "habitat": Habref,
    "nomenclature": TNomenclatures,
    "user": User,
    "taxonomy": Taxref,
    "dataset": TDatasets,
    "types_site": BibTypeSite,
    "observer_list": UserList,
    "taxonomy_list": BibListes,
    "sites_group": TMonitoringSitesGroups,
    "site": TMonitoringSites,
    "area": LAreas,
    "municipality": LiMunicipalities,
    "module": TModules,
}


# id_field_name = pk_key (trouvé avec insect)
id_field_name_dict = dict(
    (k, inspect(Model).primary_key[0].name) for (k, Model) in model_dict.items()
)

# patch municipalities
id_field_name_dict["municipality"] = "id_area"


@blueprint.route(
    "util/nomenclature/<string:code_nomenclature_type>/<string:cd_nomenclature>", methods=["GET"]
)
@json_resp
def get_util_nomenclature_api(code_nomenclature_type, cd_nomenclature):
    """
    revoie un champ d'un object de type nomenclature
        à partir de son type  et de son cd_nomenclature
    renvoie l'objet entier si field_name renseigné en paramètre de route est 'all'

    :param code_nomenclature_type:
    :param cd_nomenclature:
    :return object entier si field_name = all, la valeur du champs defini par field_name sinon
    """
    # paramètre de route
    # field_name vaut 'all' par défaut
    field_name = request.args.get("field_name", "all")

    if not hasattr(TNomenclatures, field_name) and field_name != "all":
        raise GeoNatureError("TNomenclatures n'a pas de champs {}".format(field_name))

    # requête
    try:
        res = DB.session.execute(
            select(TNomenclatures)
            .join(
                BibNomenclaturesTypes,
                and_(
                    BibNomenclaturesTypes.id_type == TNomenclatures.id_type,
                    BibNomenclaturesTypes.mnemonique == code_nomenclature_type,
                ),
            )
            .where(TNomenclatures.cd_nomenclature == cd_nomenclature)
        ).scalar_one()

        return (
            res.as_dict()
            if field_name == "all"
            else res.as_dict(
                fields=[
                    field_name,
                ]
            )
        )

    except MultipleResultsFound:
        raise GeoNatureError(
            "Nomenclature : multiple results for given type {} and code {}".format(
                code_nomenclature_type, cd_nomenclature
            )
        )

    except NoResultFound:
        raise GeoNatureError(
            "Nomenclature : no results for given type {} and code {}".format(
                code_nomenclature_type, cd_nomenclature
            )
        )


@blueprint.route("util/<string:type_util>/<string:id>", methods=["GET"])
@json_resp
def get_util_from_id_api(type_util, id):
    """
    revoie un champ d'un object de type nomenclature, taxonomy, utilisateur, ...
    renvoie l'objet entier si field_name renseigné en paramètre de route est 'all'

    :param type_util: 'nomenclature' | 'taxonomy' | 'utilisateur' | etc....
    :param id: id de l'object requis
    :type type_util: str
    :type id: str
    :return object entier si field_name = all, la valeur du champs defini par field_name sinon
    """

    # paramètre de route
    # field_name vaut 'all' par défaut
    field_name = request.args.get("field_name", "all")

    # modèle SQLA
    obj = model_dict.get(type_util)

    if not hasattr(obj, field_name) and field_name != "all":
        raise GeoNatureError("{} n'a pas de champs {}".format(type_util, field_name))

    id_field_name = request.args.get("id_field_name", id_field_name_dict.get(type_util))

    if not obj or not id_field_name:
        return None

    # requête
    try:
        res = (
            DB.session.execute(
                select(obj).where(cast(getattr(obj, id_field_name), DB.String) == id)
            )
            .unique()
            .scalar_one()
        )

        return (
            res.as_dict()
            if field_name == "all"
            else res.as_dict(
                fields=[
                    field_name,
                ]
            )
        )

    except NoResultFound:
        raise GeoNatureError("{} : no results found for id {}".format(type_util, id))
