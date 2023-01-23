import pytest
from geonature.utils.env import db

from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups


@pytest.fixture
def sites_groups():
    names = ["Site_eolien", "Site_Groupe"]

    groups = {name: TMonitoringSitesGroups(sites_group_name=name) for name in names}

    with db.session.begin_nested():
        db.session.add_all(groups.values())

    return groups


@pytest.fixture
def site_group_with_sites(sites_groups):
    return sites_groups["Site_Groupe"]


@pytest.fixture
def site_group_without_sites(sites_groups):
    return sites_groups["Site_eolien"]
