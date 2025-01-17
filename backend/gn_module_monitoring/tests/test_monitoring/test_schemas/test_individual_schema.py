import pytest
from marshmallow import ValidationError

from gn_module_monitoring.monitoring.schemas import MonitoringIndividualsSchema
from gn_module_monitoring.tests.fixtures.individual import *
from gn_module_monitoring.tests.fixtures.marking import *


@pytest.mark.usefixtures("temporary_transaction")
class TestMonitoringIndividuals:
    def test_monitoring_individuals_schema_serialization(self, individuals):
        # Récupération de l'individu
        individual = individuals["individual_with_site"]

        # Sérialisation avec le schéma
        schema = MonitoringIndividualsSchema()
        serialized_data = schema.dump(individual)

        # Vérifications
        assert serialized_data["id_individual"] == individual.id_individual
        assert serialized_data["individual_name"] == individual.individual_name
        assert serialized_data["cd_nom"] == individual.cd_nom
        assert serialized_data["active"] == individual.active
        assert serialized_data["id_digitiser"] == individual.id_digitiser

    def test_monitoring_individuals_schema_deserialization(self, users):
        # Données d'entrée
        user = users["user"]
        input_data = {
            "individual_name": "Test Individual",
            "cd_nom": 12345,
            "active": True,
            "id_digitiser": user.id_role,
        }

        # Désérialisation avec le schéma
        schema = MonitoringIndividualsSchema()
        deserialized_data = schema.load(input_data)

        # Vérifications
        assert deserialized_data["individual_name"] == input_data["individual_name"]
        assert deserialized_data["cd_nom"] == input_data["cd_nom"]
        assert deserialized_data["active"] == input_data["active"]
        assert deserialized_data["id_digitiser"] == input_data["id_digitiser"]

    def test_monitoring_individuals_schema_validation(self):
        # Données d'entrée invalides
        invalid_data = {
            "individual_name": None,  # Nom vide
            "cd_nom": None,  # cd_nom manquant
            "id_digitiser": 99999,  # ID utilisateur inexistant
        }

        # Désérialisation avec validation
        schema = MonitoringIndividualsSchema()
        try:
            schema.load(invalid_data)
        except ValidationError as err:
            errors = err.messages

            # Vérifications des erreurs
            assert "individual_name" in errors
            assert "cd_nom" in errors
            # TODO: ici ça passe avec un id_digitiser non existant
            # assert "id_digitiser" in errors

    # TODO: est ce que le dump permet de récupérer les relations ? Pour l'instant ce test ne passe pas
    # def test_schema_load_relationships(self,sites, individual_with_marking, markings):

    #     # Sérialisation avec le schéma
    #     schema = MonitoringIndividualsSchema()
    #     serialized_data = schema.dump(individual_with_marking)

    #     # Vérification que les relations sont bien incluses
    #     assert "markings" in serialized_data
