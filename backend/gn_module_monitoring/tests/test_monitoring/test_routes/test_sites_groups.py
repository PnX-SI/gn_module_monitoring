import pytest
from flask import url_for

from gn_module_monitoring.tests.fixtures.sites_groups import sites_groups


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestSitesGroups:
    def test_get_sites_groups(self, sites_groups):
        r = self.client.get(url_for("monitorings.get_sites_groups"))

        assert r.json["count"] >= len(sites_groups)
        assert all([group.as_dict() in r.json["sites_groups"] for group in sites_groups.values()])

    def test_get_sites_groups_filter_name(self, sites_groups):
        name, name_not_present = list(sites_groups.keys())

        r = self.client.get(
            url_for("monitorings.get_sites_groups"), query_string={"sites_group_name": name}
        )

        assert r.json["count"] >= 1
        json_sites_groups = r.json["sites_groups"]
        assert sites_groups[name].as_dict() in json_sites_groups
        assert sites_groups[name_not_present].as_dict() not in json_sites_groups
