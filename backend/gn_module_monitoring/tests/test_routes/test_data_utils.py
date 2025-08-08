import pytest
from flask import url_for


@pytest.mark.usefixtures("client_class")
class TestRouteDataUtils:

    def test_get_util_nomenclature_api_valid(self, install_module_test):
        code_nomenclature_type = "TYPE_MEDIA"
        cd_nomenclature = "2"

        valid_response = self.client.get(
            url_for(
                "monitorings.get_util_nomenclature_api",
                code_nomenclature_type=code_nomenclature_type,
                cd_nomenclature=cd_nomenclature,
            ),
        )
        assert valid_response.status_code == 200

    def test_get_util_nomenclature_api_invalid(self, install_module_test):
        code_nomenclature_type = "TYPE_MEDIAsss"
        cd_nomenclature = "2"

        error_response = self.client.get(
            url_for(
                "monitorings.get_util_nomenclature_api",
                code_nomenclature_type=code_nomenclature_type,
                cd_nomenclature=cd_nomenclature,
            ),
        )
        assert error_response.status_code == 500

    def test_get_util_from_id_api_valid(self, install_module_test):
        nomenclature_response = self.client.get(
            url_for(
                "monitorings.get_util_from_id_api",
                type_util="nomenclature",
                id="2",
            ),
        )
        assert nomenclature_response.status_code == 200

        user_response = self.client.get(
            url_for(
                "monitorings.get_util_from_id_api",
                type_util="user",
                id="4",
            ),
        )
        assert user_response.status_code == 200

        taxonomy_response = self.client.get(
            url_for(
                "monitorings.get_util_from_id_api",
                type_util="taxonomy",
                id="1000",
            ),
        )
        assert taxonomy_response.status_code == 200

    def test_get_util_from_id_api_invalid(self, install_module_test):
        invalid_type_response = self.client.get(
            url_for(
                "monitorings.get_util_from_id_api",
                type_util="azefazefazefazefazefze",
                id="1",
            ),
        )
        assert invalid_type_response.status_code == 204

        invalid_id_response = self.client.get(
            url_for(
                "monitorings.get_util_from_id_api",
                type_util="taxonomy",
                id="1",
            ),
        )
        assert invalid_type_response.status_code == 204
