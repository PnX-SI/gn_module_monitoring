# from pypnusershub.db.models import User
from geonature.core.taxonomie.models import Taxref

from pypnnomenclature.models import (
    TNomenclatures,
    BibNomenclaturesTypes
)
from geonature.utils.env import DB
from sqlalchemy import and_

from .utils import (
    config_from_files_customized
)


def config_data(module_path):

    return config_from_files_customized('data', module_path)


def get_data_utils(module_path):
    return {
        'nomenclature': get_nomenclature(module_path),
        'taxonomy': get_taxonomy(module_path),
        'users': {}
    }


def get_nomenclature(module_path):
    nomenclature_types = config_data(module_path).get('nomenclature')

    if not nomenclature_types:
        return {}

    q = (
        DB.session.query(TNomenclatures)
        .join(
            BibNomenclaturesTypes,
            BibNomenclaturesTypes.id_type == TNomenclatures.id_type
        )
        .filter(
            BibNomenclaturesTypes.mnemonique.in_(nomenclature_types)
        )
        .all()
    )

    return {
        d.id_nomenclature: d.as_dict()
        for d in q
    }


class CorNomListe(DB.Model):
    __tablename__ = "cor_nom_liste"
    __table_args__ = {"schema": "taxonomie"}
    id_liste = DB.Column(
        DB.Integer,
        DB.ForeignKey("taxonomie.bib_listes.id_liste"),
        nullable=False,
        primary_key=True,
    )
    id_nom = DB.Column(
        DB.Integer,
        DB.ForeignKey("taxonomie.bib_noms.id_nom"),
        nullable=False,
        primary_key=True,
    )


def get_taxonomy(module_path):
    id_list = config_data(module_path)['taxonomy'].get('id_list')
    taxonomy = get_taxonomy_from_id_list(id_list)

    return taxonomy


def get_taxonomy_from_id_list(id_list):

    if not id_list:
        return {}

    id_list
    q = (
        DB.session.query(Taxref)
        .join(
            CorNomListe,
            and_(
                CorNomListe.id_liste == id_list,
                CorNomListe.id_nom == Taxref.cd_nom
            )
        )
        .join()
        .all()
    )

    return {
        (d.cd_nom): (d.nom_complet)
        for d in q
    }


def get_users(module_path):
    return {}
    pass
