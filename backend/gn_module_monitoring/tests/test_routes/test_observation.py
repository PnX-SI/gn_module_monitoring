from datetime import datetime

from gn_module_monitoring.tests.fixtures.module import install_monitoring_module
import pytest

from flask import current_app, url_for

from pypnusershub.tests.utils import set_logged_user_cookie
from geonature.utils.env import db, BACKEND_DIR
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringVisits,
    TMonitoringObservations,
)
from sqlalchemy import select

from apptax.taxonomie.models import BibListes
from pypnusershub.db.models import UserList


@pytest.fixture
def module_test_observation(types_site, users):
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
def observation_data(sites, datasets, module_test_observation, users):
    visit_date_min = datetime.strptime("2025-01-01", "%Y-%m-%d").date()
    dataset = datasets["orphan_dataset"]

    db_observations = []
    for site in sites.values():
        visit = TMonitoringVisits(
            id_base_site=site.id_base_site,
            id_module=module_test_observation.id_module,
            id_dataset=dataset.id_dataset,
            visit_date_min=visit_date_min,
        )
        with db.session.begin_nested():
            db.session.add(visit)
        db_observations.append(
            TMonitoringObservations(
                id_base_visit=visit.id_base_visit,
                cd_nom=103536,  # Illecebrum verticillatum
                id_digitiser=users["admin_user"].id_role,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(db_observations)
    db.session.flush()
    return db_observations


@pytest.mark.usefixtures("client_class", "observation_data")
class TestObservations:

    def test_get_observation(self, observation_data, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_observations",
                module_code="test",
            )
        )
        expected_obs = {obs.id_observation for obs in observation_data}
        current_obs = {obs["id_observation"] for obs in r.json["items"]}
        assert expected_obs.issubset(current_obs)
        assert all(obs["cd_nom"] is not None for obs in r.json["items"])

    def test_get_observations_with_site(self, observation_data, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        id_base_visit = observation_data[0].id_base_visit

        r = self.client.get(
            url_for(
                "monitorings.get_observations",
                module_code="test",
                id_base_visit=id_base_visit,
            )
        )

        expected_observations = {
            observation.id_observation
            for observation in observation_data
            if observation.id_base_visit == id_base_visit
        }
        current_observations = {observation["id_observation"] for observation in r.json["items"]}

        assert expected_observations.issubset(current_observations)

    def test_get_observations_with_cd_nom(self, observation_data, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        cd_nom = observation_data[0].cd_nom

        expected_observations = {
            observation.id_observation
            for observation in observation_data
            if observation.cd_nom == cd_nom
        }
        # Filter cd_nom as integer
        r = self.client.get(
            url_for(
                "monitorings.get_observations",
                module_code="test",
                cd_nom=cd_nom,
            )
        )
        current_observations = {observation["id_observation"] for observation in r.json["items"]}
        assert expected_observations.issubset(current_observations)

        # Filter cd_nom as string
        r = self.client.get(
            url_for(
                "monitorings.get_observations",
                module_code="test",
                cd_nom="ill",
            )
        )
        current_observations = {observation["id_observation"] for observation in r.json["items"]}

        assert expected_observations.issubset(current_observations)

    def test_get_observation_by_id(self, observation_data, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        observation = observation_data[0]

        r = self.client.get(
            url_for(
                "monitorings.get_observation_by_id",
                module_code="test",
                id=observation.id_observation,
            )
        )

        assert r.status_code == 200
        assert r.json["id_observation"] == observation.id_observation

    def test_get_observation_by_id_not_found(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for(
                "monitorings.get_observation_by_id",
                module_code="test",
                id=999999999,
            )
        )

        assert r.status_code == 404

    def test_post_observation(self, observation_data, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        visit = observation_data[0].visit

        data = {
            "id_base_visit": visit.id_base_visit,
            "id_digitiser": users["admin_user"].id_role,
            "cd_nom": 114114,
        }

        r = self.client.post(
            url_for(
                "monitorings.post_observation",
                module_code="test",
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["id_base_visit"] == visit.id_base_visit
        assert r.json["cd_nom"] == data["cd_nom"]

    def test_patch_observation(self, observation_data, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        data = {
            "cd_nom": 85740,
        }

        r = self.client.patch(
            url_for(
                "monitorings.patch_observation",
                module_code="test",
                _id=observation_data[0].id_observation,
            ),
            json=data,
        )
        assert r.status_code == 200
        assert r.json["cd_nom"] == data["cd_nom"]

    def test_patch_observation_not_found(self, observation_data, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        module_code = "test"

        r = self.client.patch(
            url_for(
                "monitorings.patch_observation",
                module_code=module_code,
                _id=999999999,
            ),
            json={},
        )

        assert r.status_code == 404

    def test_delete_observation(self, observation_data, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        observation = observation_data[-1]

        r = self.client.delete(
            url_for(
                "monitorings.delete_observation",
                _id=observation.id_observation,
                module_code="test",
            )
        )

        assert r.status_code == 200
        assert r.json == {"success": "Item is successfully deleted"}

        r = self.client.get(
            url_for(
                "monitorings.get_observation_by_id",
                module_code="test",
                id=observation.id_observation,
            )
        )
        assert r.status_code == 404

    def test_delete_observation_not_found(self, observation_data, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.delete(
            url_for("monitorings.delete_observation", _id=999999999, module_code="test")
        )

        assert r.status_code == 404
