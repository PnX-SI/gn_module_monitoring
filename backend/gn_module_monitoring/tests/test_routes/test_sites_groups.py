import pytest
from flask import url_for

from sqlalchemy import select

from geonature.utils.env import db

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema

from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestSitesGroups:
    def test_get_sites_group_by_id(self, sites_groups, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
        sites_group = list(sites_groups.values())[0]
        id_sites_group = sites_group.id_sites_group
        r = self.client.get(
            url_for("monitorings.get_sites_group_by_id", id_sites_group=id_sites_group)
        )

        assert r.json["id_sites_group"] == id_sites_group
        assert r.json["sites_group_name"] == sites_group.sites_group_name

    def test_get_sites_groups(self, sites_groups, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
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

    def test_get_sites_groups_filter_name(self, sites_groups, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
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

    def test_get_sites_groups_geometries(self, sites, site_group_with_sites, monitorings_users):
        set_logged_user_cookie(self.client, monitorings_users["admin_user"])
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
