import pytest
from geoalchemy2.shape import from_shape
from geonature.utils.env import db
from shapely.geometry import Point

from gn_module_monitoring.monitoring.models import TMonitoringSites


@pytest.fixture()
def sites(users, types_site, site_group_with_sites):
    user = users["user"]
    geom_4326 = from_shape(Point(43, 24), srid=4326)
    sites = {}
    for i, key in enumerate(types_site.keys()):
        sites[key] = TMonitoringSites(
            id_inventor=user.id_role,
            id_digitiser=user.id_role,
            base_site_name=f"Site{i}",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_4326,
            id_nomenclature_type_site=types_site[key].id_nomenclature_type_site,
            types_site=[types_site[key]],
            id_sites_group=site_group_with_sites.id_sites_group,
        )
    with db.session.begin_nested():
        db.session.add_all(sites.values())
    return sites
