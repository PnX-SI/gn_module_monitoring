import pytest

from flask import url_for
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from sqlalchemy import select

from geonature.utils.env import db

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups, TMonitoringModules
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema
from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class")
class TestSitesGroups:

    def test_get_sites_group_by_id(self, sites_groups, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        sites_group = list(sites_groups.values())[0]
        id_sites_group = sites_group.id_sites_group
        r = self.client.get(
            url_for("monitorings.get_sites_group_by_id", id_sites_group=id_sites_group)
        )

        assert r.json["id_sites_group"] == id_sites_group
        assert r.json["sites_group_name"] == sites_group.sites_group_name

    def test_get_sites_groups(self, sites_groups, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(url_for("monitorings.get_sites_groups"))

        assert r.json["count"] >= len(sites_groups)

        sites_group_response = r.json["items"]
        for s in sites_group_response:
            s.pop("cruved")

        assert all(
            [
                MonitoringSitesGroupsSchema().dump(group) in sites_group_response
                for group in sites_groups.values()
            ]
        )

    def test_get_sites_groups_filter_name(self, sites_groups, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        name, name_not_present = list(sites_groups.keys())
        schema = MonitoringSitesGroupsSchema()

        r = self.client.get(
            url_for("monitorings.get_sites_groups"), query_string={"sites_group_name": name}
        )

        assert r.json["count"] >= 1
        json_sites_groups = r.json["items"]

        # Suppression du cruved
        for s in json_sites_groups:
            s.pop("cruved")

        assert schema.dump(sites_groups[name]) in json_sites_groups
        assert schema.dump(sites_groups[name_not_present]) not in json_sites_groups

    def test_serialize_sites_groups(self, sites_groups, sites):
        groups = db.session.scalars(
            select(TMonitoringSitesGroups).where(
                TMonitoringSitesGroups.id_sites_group.in_(
                    [s.id_sites_group for s in sites_groups.values()]
                )
            )
        ).all()
        schema = MonitoringSitesGroupsSchema()
        assert [schema.dump(site) for site in groups]

    def test_get_sites_groups_geometries(self, sites, site_group_with_sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(url_for("monitorings.get_sites_group_geometries"))

        json_resp = r.json
        features = json_resp.get("features")
        assert r.content_type == "application/json"
        assert json_resp.get("type") == "FeatureCollection"
        assert len(features) >= 1
        id_ = [
            obj["properties"]
            for obj in features
            if obj["properties"]["sites_group_name"] == site_group_with_sites.sites_group_name
        ][0]["id_sites_group"]
        assert id_ == site_group_with_sites.id_sites_group


# TODO: ajouter tests sur tri
# TODO: ajouter tests sur filtre par permissions
@pytest.mark.usefixtures("client_class", "temporary_transaction", "install_module_test")
class TestSitesGroupsWithModule:

    def test_get_module_groups(self, test_module_user, add_group):
        set_logged_user_cookie(self.client, test_module_user)
        meteo = self._get_meteo_value("Beau")
        groups = []
        for _ in range(3):
            groups.append(
                add_group(
                    data={
                        "group_specific": "specific text for group",
                        "group_specific_meteo": meteo.id_nomenclature,
                    }
                )
            )

        response = self.client.get(url_for("monitorings.get_sites_groups", module_code="test"))

        assert response.status_code == 200
        groups_repr = response.json["items"]
        assert len(groups_repr) == 3
        groups_repr_ids = [g["id_sites_group"] for g in groups_repr]
        for expected_group in groups:
            assert expected_group.id_sites_group in groups_repr_ids

        group_repr = groups_repr[0]
        # Attribut spécifique du groupe est présent
        assert group_repr.get("group_specific") == "specific text for group"
        # ID retourné pour attribut spécifique du groupe
        assert group_repr.get("group_specific_meteo") == meteo.id_nomenclature

    def test_get_module_groups_with_filter_on_generic_attribute(self, test_module_user, add_group):
        set_logged_user_cookie(self.client, test_module_user)
        group = add_group(sites_group_name="Grottes")
        add_group(sites_group_name="Arbres")
        filter_params = {"sites_group_name": "gr"}

        response = self.client.get(
            url_for("monitorings.get_sites_groups", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        groups_response = response.json["items"]
        assert len(groups_response) == 1
        group_repr = groups_response[0]
        assert group_repr["id_sites_group"] == group.id_sites_group

    def test_get_module_groups_with_filter_on_group_specific_attribute(
        self, test_module_user, add_group
    ):
        set_logged_user_cookie(self.client, test_module_user)
        filter_params = {"group_specific": "foo"}
        group = add_group(data={"group_specific": "foo"})  # Sera retourné avec le filtre
        add_group(data={"group_specific": "bar"})  # Non retourné avec le filtre

        response = self.client.get(
            url_for("monitorings.get_sites_groups", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        groups_response = response.json["items"]
        assert len(groups_response) == 1
        groups_ids = [s["id_sites_group"] for s in groups_response]
        assert group.id_sites_group in groups_ids

    def test_get_module_groups_with_filter_on_group_specific_nomenclature_attribute(
        self, test_module_user, add_group
    ):
        set_logged_user_cookie(self.client, test_module_user)
        beau = self._get_meteo_value("Beau")
        mauvais = self._get_meteo_value("Mauvais")
        filter_params = {"group_specific_meteo": "mauv"}
        group = add_group(data={"group_specific_meteo": mauvais.id_nomenclature})  # match
        add_group(data={"group_specific_meteo": beau.id_nomenclature})  # no match
        add_group()  # empty "meteo" => no match

        response = self.client.get(
            url_for("monitorings.get_sites_groups", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        groups_response = response.json["items"]
        assert len(groups_response) == 1
        groups_ids = [s["id_sites_group"] for s in groups_response]
        assert group.id_sites_group in groups_ids

    @staticmethod
    def _get_meteo_value(mnemonique):
        return db.session.execute(
            select(TNomenclatures)
            .join(BibNomenclaturesTypes)
            .where(BibNomenclaturesTypes.mnemonique == "TEST_METEO")
            .where(TNomenclatures.mnemonique == mnemonique)
        ).scalar()

    @pytest.mark.usefixtures("install_module_test")
    @pytest.fixture
    def add_group(self, test_module_user):

        def _add_group(**kwargs):
            _add_group.counter += 1
            i = _add_group.counter
            user = test_module_user
            module = db.session.execute(
                select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
            ).scalar()

            args = {
                "id_digitiser": user.id_role,
                "sites_group_name": f"SitesGroupName{i}",
                "sites_group_description": f"SitesGroupDescription{i}",
                "sites_group_code": f"SitesGroupCode{i}",
            }
            args.update(**kwargs)
            site = TMonitoringSitesGroups(**args)
            site.modules.append(module)
            with db.session.begin_nested():
                db.session.add(site)
            return site

        _add_group.counter = 0

        return _add_group
