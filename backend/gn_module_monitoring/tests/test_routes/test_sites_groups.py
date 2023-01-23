import pytest
from flask import url_for

from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups
from gn_module_monitoring.monitoring.schemas import MonitoringSitesGroupsSchema


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestSitesGroups:
    def test_get_sites_groups(self, sites_groups):
        r = self.client.get(url_for("monitorings.get_sites_groups"))

        assert r.json["count"] >= len(sites_groups)
        assert all(
            [
                MonitoringSitesGroupsSchema().dump(group) in r.json["items"]
                for group in sites_groups.values()
            ]
        )

    def test_get_sites_groups_filter_name(self, sites_groups):
        name, name_not_present = list(sites_groups.keys())
        schema = MonitoringSitesGroupsSchema()

        r = self.client.get(
            url_for("monitorings.get_sites_groups"), query_string={"sites_group_name": name}
        )

        assert r.json["count"] >= 1
        json_sites_groups = r.json["items"]
        assert schema.dump(sites_groups[name]) in json_sites_groups
        assert schema.dump(sites_groups[name_not_present]) not in json_sites_groups

    def test_serialize_sites_groups(self, sites_groups, sites):
        groups = TMonitoringSitesGroups.query.filter(
            TMonitoringSitesGroups.id_sites_group.in_(
                [s.id_sites_group for s in sites_groups.values()]
            )
        ).all()
        schema = MonitoringSitesGroupsSchema()
        assert [schema.dump(site) for site in groups]

    def test_get_sites_groups_geometries(self, sites, site_group_with_sites):
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
