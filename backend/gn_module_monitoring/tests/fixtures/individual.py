import pytest

from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from geonature.utils.env import db
from apptax.taxonomie.models import Taxref

from geonature.core.gn_monitoring.models import corIndividualModule
from gn_module_monitoring.monitoring.models import TMonitoringIndividuals
from gn_module_monitoring.tests.fixtures.marking import *

SPECIE = "Athene noctua"


@pytest.fixture
def individuals(monitorings_users, monitoring_module):
    user = monitorings_users["user"]
    cd_nom = db.session.execute(
        select(Taxref.cd_nom).where(
            and_(Taxref.lb_nom.ilike(SPECIE), Taxref.cd_nom == Taxref.cd_ref)
        )
    ).scalar_one_or_none()
    if cd_nom is None:
        raise ValueError(f"L'espèce '{SPECIE}' n'a pas été trouvée dans la table Taxref.")

    db_individuals = {}
    cor_individual_module = []
    individuals_key = ["individual_with_site", "orphan_individual"]

    for key in individuals_key:
        db_individuals[key] = TMonitoringIndividuals(
            individual_name=key,
            cd_nom=cd_nom,
            active=True,
            id_digitiser=user.id_role,
        )
    # Insertion des individus dans la base de données
    with db.session.begin_nested():
        db.session.add_all(db_individuals.values())
        db.session.flush()

        for key in individuals_key:
            cor_individual_module.append(
                {
                    "id_individual": db_individuals[
                        key
                    ].id_individual,  # Maintenant, l'ID est disponible
                    "id_module": monitoring_module.id_module,
                }
            )

        # Insertion dans la table de relation corIndividualModule
        db.session.execute(corIndividualModule.insert(), cor_individual_module)

    return db_individuals


# TODO: a enlever si pas besoin du tests pour les relationship avec TMonitoringIndividuals
@pytest.fixture
def individual_with_marking(individuals, markings):
    individual = (
        db.session.query(TMonitoringIndividuals)
        .options(joinedload(TMonitoringIndividuals.markings))
        .filter(
            TMonitoringIndividuals.id_individual
            == individuals["individual_with_site"].id_individual
        )
        .one()
    )
    return individual
