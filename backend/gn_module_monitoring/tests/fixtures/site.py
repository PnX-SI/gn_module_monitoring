import pytest
from geoalchemy2.shape import from_shape
from geonature.utils.env import db
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures
from shapely.geometry import Point

from gn_module_monitoring.monitoring.models import BibCategorieSite, TMonitoringSites
from gn_module_monitoring.tests.fixtures.sites_groups import sites_groups


@pytest.fixture()
def site_type():
    return TNomenclatures.query.filter(
            BibNomenclaturesTypes.mnemonique == "TYPE_SITE", TNomenclatures.mnemonique == "Grotte"
        ).one()


@pytest.fixture()
def categories(site_type):
    categories = [
        {"label": "gite", "config": {}, "site_type": [site_type]},
        {"label": "eolienne", "config": {}, "site_type": [site_type]},
    ]

    categories = {cat["label"]: BibCategorieSite(**cat) for cat in categories}

    with db.session.begin_nested():
        db.session.add_all(categories.values())

    return categories


@pytest.fixture()
def sites(users, categories, sites_groups):
    user = users["user"]
    geom_4326 = from_shape(Point(43, 24), srid=4326)
    sites = {}
    # TODO: get_nomenclature from label
    site_type = TNomenclatures.query.filter(
        BibNomenclaturesTypes.mnemonique == "TYPE_SITE", TNomenclatures.mnemonique == "Grotte"
    ).one()
    for i, key in enumerate(categories.keys()):
        sites[key] = TMonitoringSites(
            id_inventor=user.id_role,
            id_digitiser=user.id_role,
            base_site_name=f"Site{i}",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_4326,
            id_nomenclature_type_site=site_type.id_nomenclature,
            id_categorie=categories[key].id_categorie,
            id_sites_group=sites_groups["Site_Groupe"].id_sites_group,
        )
    with db.session.begin_nested():
        db.session.add_all(sites.values())
    return sites
