from datetime import datetime

from gn_module_monitoring.tests.fixtures.module import install_monitoring_module
import pytest

from flask import current_app, url_for

from pypnusershub.tests.utils import set_logged_user_cookie
from geonature.utils.env import db, BACKEND_DIR
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringObservationDetails,
    TMonitoringObservations,
    TMonitoringVisits,
)
from sqlalchemy import select

from apptax.taxonomie.models import BibListes
from pypnusershub.db.models import UserList


@pytest.fixture
def module_test_visit(types_site, users):
    install_monitoring_module("test", types_site, users)
    module_test = db.session.execute(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one_or_none()

    with db.session.begin_nested():
        module_test.id_list_taxonomy = db.session.scalar(select(BibListes.id_liste).limit(1))
        module_test.id_list_observer = db.session.scalar(select(UserList.id_liste).limit(1))
        module_test.taxonomy_display_field_name = "nom_vern,lb_nom"
        db.session.add(module_test)
    return module_test


@pytest.fixture
def visits_routes(sites, datasets, module_test_visit):
    visit_date_min = datetime.strptime("2025-01-01", "%Y-%m-%d").date()
    dataset = datasets["orphan_dataset"]
    db_visits = []
    for site in sites.values():
        db_visits.append(
            TMonitoringVisits(
                id_base_site=site.id_base_site,
                id_module=module_test_visit.id_module,
                id_dataset=dataset.id_dataset,
                visit_date_min=visit_date_min,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_visits)
    db.session.flush()
    return db_visits


@pytest.fixture
def observation(visits_routes, users):
    admin_user = users["admin_user"]
    visit = visits_routes[0]
    db_observation = TMonitoringObservations(
        id_base_visit=visit.id_base_visit,
        cd_nom=67111,
        id_digitiser=admin_user.id_role,
    )
    with db.session.begin_nested():
        db.session.add(db_observation)
    return db_observation


@pytest.fixture
def obs_details(observation):
    fake_datas = [
        {"nom_contact": "nom_value", "prenom_contact": "prenom_value"},
        {"nom_contact": "nom_value_2", "prenom_contact": "prenom_value_2"},
    ]
    obs_details = []
    for data in fake_datas:
        db_obs_detail = TMonitoringObservationDetails(
            id_observation=observation.id_observation,
            data=data,
        )
        with db.session.begin_nested():
            db.session.add(db_obs_detail)
        obs_details.append(db_obs_detail)

    return obs_details


@pytest.mark.usefixtures("client_class")
class TestObservationDetails:

    def test_get_obs_details(self, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_obs_details",
                module_code="test",
            )
        )

        expected_obs_details = {detail.id_observation_detail for detail in obs_details}
        current_obs_details = {
            obs_detail["id_observation_detail"] for obs_detail in r.json["items"]
        }
        assert expected_obs_details.issubset(current_obs_details)

    def test_get_obs_details_with_obs(self, observation, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for(
                "monitorings.get_obs_details",
                module_code="test",
                id_observation=observation.id_observation,
            ),
        )

        expected_obs_details = {
            detail.id_observation_detail
            for detail in obs_details
            if detail.id_observation == observation.id_observation
        }
        current_obs_details = {
            obs_detail["id_observation_detail"] for obs_detail in r.json["items"]
        }
        print("expected_obs_details", expected_obs_details)
        print("current_obs_details", current_obs_details)
        assert expected_obs_details.issubset(current_obs_details)

    def test_get_obs_detail_by_id(self, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        obs_detail_instance = obs_details[0]

        r = self.client.get(
            url_for(
                "monitorings.get_obs_detail_by_id",
                module_code="test",
                id=obs_detail_instance.id_observation_detail,
            )
        )

        assert r.status_code == 200
        assert r.json["id_observation_detail"] == obs_detail_instance.id_observation_detail
        # `module` is explicitly excluded from the schema in get_obs_detail_by_id
        assert "module" not in r.json

    def test_get_obs_detail_by_id_not_found(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for(
                "monitorings.get_obs_detail_by_id",
                module_code="test",
                id=999999999,
            )
        )

        assert r.status_code == 404

    def test_post_obs_detail(self, observation, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        obs_detail_instance = obs_details[0]

        data = {
            "id_observation": observation.id_observation,
            "nom_contact": "new_nom_value",
            "prenom_contact": "new_prenom_value",
        }

        r = self.client.post(
            url_for(
                "monitorings.post_obs_detail",
                module_code="test",
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_observation"] == obs_detail_instance.id_observation
        assert r.json["nom_contact"] == data["nom_contact"]
        assert r.json["prenom_contact"] == data["prenom_contact"]

    def test_patch_obs_detail(self, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        obs_detail_instance = obs_details[0]

        data = {
            "id_observation_detail": obs_detail_instance.id_observation_detail,
            "nom_contact": "updated_nom_value",
            "prenom_contact": "updated_prenom_value",
        }

        r = self.client.patch(
            url_for(
                "monitorings.patch_obs_detail",
                object_type="observation_detail",
                module_code="test",
                _id=obs_detail_instance.id_observation_detail,
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_observation_detail"] == obs_detail_instance.id_observation_detail
        assert r.json["nom_contact"] == data["nom_contact"]
        assert r.json["prenom_contact"] == data["prenom_contact"]

    def test_patch_obs_detail_not_found(self, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        module_code = "test"

        r = self.client.patch(
            url_for(
                "monitorings.patch_obs_detail",
                object_type="observation_detail",
                module_code=module_code,
                _id=999999999,
            ),
            json={},
        )

        assert r.status_code == 404

    def test_delete_obs_detail(self, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        obs_detail_instance = obs_details[-1]

        r = self.client.delete(
            url_for(
                "monitorings.delete_obs_detail",
                object_type="observation_detail",
                module_code="test",
                _id=obs_detail_instance.id_observation_detail,
            )
        )

        assert r.status_code == 200
        assert r.json == {"success": "Item is successfully deleted"}

        r = self.client.get(
            url_for(
                "monitorings.get_obs_detail_by_id",
                module_code="test",
                id=obs_detail_instance.id_observation_detail,
                object_type="observation_detail",
            )
        )
        assert r.status_code == 404

    def test_delete_obs_detail_not_found(self, obs_details, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.delete(
            url_for("monitorings.delete_obs_detail", _id=999999999, module_code="test")
        )

        assert r.status_code == 404
