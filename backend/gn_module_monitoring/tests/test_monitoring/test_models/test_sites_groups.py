import pytest

from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups


@pytest.mark.usefixtures("temporary_transaction")
class TestTMonitoringSitesGroups:
    def test_sort_desc(self, sites_groups):
        if len(sites_groups) < 2:
            pytest.xfail(
                "This test cannot work if there is less than 2 sites_groups in database (via fixtures or not)"
            )

        query = TMonitoringSitesGroups.query.filter(
            TMonitoringSitesGroups.id_sites_group.in_(
                group.id_sites_group for group in sites_groups.values()
            )
        ).sort(label="id_sites_group", direction="desc")
        result = query.all()

        assert result[0].id_sites_group > result[1].id_sites_group

    def test_sort_asc(self, sites_groups):
        if len(sites_groups) < 2:
            pytest.xfail(
                "This test cannot work if there is less than 2 sites_groups in database (via fixtures or not)"
            )

        query = TMonitoringSitesGroups.query.filter(
            TMonitoringSitesGroups.id_sites_group.in_(
                group.id_sites_group for group in sites_groups.values()
            )
        ).sort(label="id_sites_group", direction="asc")
        result = query.all()

        assert result[0].id_sites_group < result[1].id_sites_group
