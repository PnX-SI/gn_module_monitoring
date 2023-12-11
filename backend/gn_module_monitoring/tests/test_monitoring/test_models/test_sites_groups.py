import pytest

from sqlalchemy.sql.expression import select
from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups


from geonature.utils.env import DB


@pytest.mark.usefixtures("temporary_transaction")
class TestTMonitoringSitesGroups:
    def test_sort_desc(self, sites_groups):
        if len(sites_groups) < 2:
            pytest.xfail(
                "This test cannot work if there is less than 2 sites_groups in database (via fixtures or not)"
            )

        query = (
            select(TMonitoringSitesGroups)
            .filter(
                TMonitoringSitesGroups.id_sites_group.in_(
                    group.id_sites_group for group in sites_groups.values()
                )
            )
            .order_by(TMonitoringSitesGroups.id_sites_group.desc())
        )
        result = DB.session.scalars(query).all()

        assert result[0].id_sites_group > result[1].id_sites_group

    def test_sort_asc(self, sites_groups):
        if len(sites_groups) < 2:
            pytest.xfail(
                "This test cannot work if there is less than 2 sites_groups in database (via fixtures or not)"
            )

        query = (
            select(TMonitoringSitesGroups)
            .filter(
                TMonitoringSitesGroups.id_sites_group.in_(
                    group.id_sites_group for group in sites_groups.values()
                )
            )
            .order_by(TMonitoringSitesGroups.id_sites_group.asc())
        )
        result = DB.session.scalars(query).all()

        assert result[0].id_sites_group < result[1].id_sites_group
