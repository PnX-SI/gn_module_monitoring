"""
    Routes pour récupérer des paramètre
        d'utilisateurs
        de nomenclature
        de taxonomie

        TODO cache
"""

from flask import request
from sqlalchemy import and_, inspect
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from geonature.core.taxonomie.models import Taxref, BibListes
from geonature.core.users.models import TListes

from pypnusershub.db.models import User


from utils_flask_sqla.response import json_resp

from geonature.core.gn_meta.models import TDatasets
from geonature.utils.env import DB

from geonature.utils.errors import GeoNatureError

from ..blueprint import blueprint

from ..monitoring.models import TMonitoringSitesGroups

model_dict = {
    'nomenclature': TNomenclatures,
    'user': User,
    'taxonomy': Taxref,
    'dataset': TDatasets,
    'observer_list': TListes,
    'taxonomy_list': BibListes,
    'sites_group': TMonitoringSitesGroups,
    }

id_field_name_dict = dict( 
    (k, inspect(Model).primary_key[0].name)
    for (k, Model) in model_dict.items()
)


@blueprint.route('util/nomenclature/<string:code_nomenclature_type>/<string:cd_nomenclature>', methods=['GET'])
@json_resp
def get_util_nomenclature_api(code_nomenclature_type, cd_nomenclature):
    '''
        revoie un champ d'un object de type nomenclature
            à partir de son type  et de son cd_nomenclature
        renvoie l'objet entier si field_name renseigné en paramètre de route est 'all'

        :param code_nomenclature_type:
        :param cd_nomenclature:
        :return object entier si field_name = all, la valeur du champs defini par field_name sinon
    '''
    # paramètre de route
    # field_name vaut 'all' par défaut
    field_name = request.args.get('field_name', 'all')

    if not hasattr(TNomenclatures, field_name) and field_name != "all":
        raise GeoNatureError(
            "TNomenclatures n'a pas de champs {}"
            .format(field_name)
            )

    try:
        scope = TNomenclatures if field_name == 'all' else getattr(TNomenclatures, field_name)
        res = (
            DB.session.query(scope)
            .join(
                BibNomenclaturesTypes,
                and_(
                    BibNomenclaturesTypes.id_type == TNomenclatures.id_type,
                    BibNomenclaturesTypes.mnemonique == code_nomenclature_type
                )
            )
            .filter(TNomenclatures.cd_nomenclature == cd_nomenclature)
            .one()
        )

        return res.as_dict() if field_name == 'all' else res[0]

    except MultipleResultsFound:
        raise GeoNatureError(
            'Nomenclature : multiple results for given type {} and code {}'
            .format(code_nomenclature_type, cd_nomenclature)
        )

    except NoResultFound:
        raise GeoNatureError(
            'Nomenclature : no results for given type {} and code {}'
            .format(code_nomenclature_type, cd_nomenclature)
        )


@blueprint.route('util/<string:type_util>/<int:id>', methods=['GET'])
@json_resp
def get_util_from_id_api(type_util, id):
    '''
        revoie un champ d'un object de type nomenclature, taxonomy, utilisateur, ...
        renvoie l'objet entier si field_name renseigné en paramètre de route est 'all'

        :param type_util: 'nomenclaure' | 'taoxonomy' | 'utilisateur'
        :param id: id de l'object requis
        :type type_util: str
        :type id: int
        :return object entier si field_name = all, la valeur du champs defini par field_name sinon
    '''

    # paramètre de route
    # field_name vaut 'all' par défaut
    field_name = request.args.get('field_name', 'all')

    # modèle SQLA
    obj = model_dict.get(type_util)

    if not hasattr(obj, field_name) and field_name != "all":
        raise GeoNatureError(
            "{} n'a pas de champs {}"
            .format(type_util, field_name)
        )

    id_field_name = id_field_name_dict.get(type_util)

    if not obj or not id_field_name:
        return None

    scope = obj if field_name == 'all' else getattr(obj, field_name)
    # requête
    try:
        res = (
            DB.session.query(scope)
            .filter(getattr(obj, id_field_name) == id)
            .one()
        )

        return res.as_dict() if field_name == 'all' else res[0]

    except NoResultFound:
        raise GeoNatureError(
            '{} : no results found for id {}'
            .format(type_util, id)
        )


@blueprint.route('util/<string:type_util>/<string:ids>', methods=['GET'])
@json_resp
def get_util_from_ids_api(type_util, ids):
    '''
        variante de get_util_from_id_api pour plusieurs id
        renvoie un tableau de valeur (ou de dictionnaire si key est 'all')

        parametre get
            key: all renvoie tout l'objet
                sinon renvoie un champ
            separator_out:
                pour reformer une chaine de caractere a partir du tableau résultat de la requete
                si separator_out == ' ,'
                alors ['jean', 'pierre', 'paul'].join(separator_out) -> 'jean, pierre, paul'

        :param type_util: 'nomenclaure' | 'taoxonomy' | 'utilisateur'
        :param ids: plusieurs id reliée par des '-' (ex: 1-123-3-4)
        :type type_util: str
        :type ids: str
        :return list si key=all ou chaine de caratere

    '''

    field_name = request.args.get('field_name', 'all')
    separator_out = request.args.get('sep_out', ', ')

    # tableau d'id depuis ids
    list_ids = list(ids.split('-'))

    obj = model_dict.get(type_util)
    id_field_name = id_field_name_dict.get(type_util)

    if not hasattr(obj, field_name) and field_name != "all":
        raise GeoNatureError(
            "{} n'a pas de champs {}"
            .format(type_util, field_name)
        )

    # requête
    scope = obj if field_name == 'all' else getattr(obj, field_name)
    res = (
        DB.session.query(scope)
        .filter(
            getattr(obj, id_field_name).in_(list_ids)
        )
        .all()
    )

    if len(res) != len(list_ids):
        raise GeoNatureError(
            '{} : pas toutes les id trouvées parmis {}'
            .format(type_util, ids))

    if field_name == 'all':
        return [r.as_dict() for r in res]

    # renvoie une chaine de caratère
    return separator_out.join([r[0] for r in res])
