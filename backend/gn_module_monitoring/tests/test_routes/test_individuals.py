import pytest
from flask import url_for

from geonature.utils.env import db
from geonature.core.gn_permissions.models import (
    PermAction,
    PermObject,
    Permission,
)

from io import StringIO
import pandas as pd
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.tests.fixtures.generic import *
from gn_module_monitoring.tests.fixtures.individual import *


@pytest.mark.usefixtures("client_class")
class TestIndividuals:

    def test_get_individuals(self, install_module_test_indi, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        individuals = install_module_test_indi
        id_individuals = [i.id_individual for i in individuals]

        # Test get with default sort
        response = self.client.get(url_for("monitorings.get_individuals", module_code="test_indi"))
        assert response.status_code == 200
        individuals_response = response.json["items"]

        assert len(individuals_response) == 3
        assert individuals_response[0]["id_individual"] == max(id_individuals)

        # Test sort asc
        response = self.client.get(
            url_for("monitorings.get_individuals", module_code="test_indi", sort_dir="asc")
        )
        individuals_response = response.json["items"]

        assert individuals_response[0]["id_individual"] == min(id_individuals)

        # Test sort other column
        response = self.client.get(
            url_for(
                "monitorings.get_individuals",
                module_code="test_indi",
                sort="comment",
                sort_dir="asc",
            )
        )
        individuals_response = response.json["items"]
        assert len(individuals_response) == 3
        assert individuals_response[0]["comment"] == "A Super lézard"

        # Test filter main column
        response = self.client.get(
            url_for("monitorings.get_individuals", module_code="test_indi", id_digitiser="Bob")
        )
        individuals_response = response.json["items"]
        assert len(individuals_response) == 2
        assert individuals_response[0]["id_digitiser"] == users["user"].id_role

        # Test filter cd_nom column
        response = self.client.get(
            url_for("monitorings.get_individuals", module_code="test_indi", cd_nom=649883)
        )
        individuals_response = response.json["items"]
        assert len(individuals_response) == 1
        assert individuals_response[0]["cd_nom"] == 649883

        response = self.client.get(
            url_for("monitorings.get_individuals", module_code="test_indi", cd_nom="python")
        )
        individuals_response = response.json["items"]
        assert len(individuals_response) == 1
        assert individuals_response[0]["cd_nom"] == 649883
