import pytest
from geoalchemy2.shape import from_shape
from geonature.utils.env import db
from shapely.geometry import Point

from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema


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

    # Add a special site that has no type
    sites["no-type"] = TMonitoringSites(
        id_inventor=user.id_role,
        id_digitiser=user.id_role,
        base_site_name=f"no-type",
        base_site_description=f"Description-no-type",
        base_site_code=f"Code-no-type",
        geom=geom_4326,
        # Random id_nomenclature_type_site
        # FIXME: when id_nomenclature_type_site disapears => remove this line
        id_nomenclature_type_site=list(types_site.values())[0].id_nomenclature_type_site,
        types_site=[],
        id_sites_group=site_group_with_sites.id_sites_group,
    )

    with db.session.begin_nested():
        db.session.add_all(sites.values())
    return sites


@pytest.fixture()
def site_to_post_with_types(users, types_site, site_group_without_sites):
    user = users["user"]
    geom_4326 = from_shape(Point(43, 24), srid=4326)
    list_nomenclature_id = []
    specific_dic = {"owner_name": "Propriétaire", "threat": "Menaces", "owner_tel": "0609090909"}
    schema_type_site = BibTypeSiteSchema()
    mock_db_type_site = [schema_type_site.dump(type) for type in types_site.values()]

    for type in mock_db_type_site:
        list_nomenclature_id.append(type["id_nomenclature_type_site"])

    site_to_post_with_types = TMonitoringSites(
        id_inventor=user.id_role,
        id_digitiser=user.id_role,
        base_site_name=f"New Site",
        base_site_description=f"New Description",
        base_site_code=f"New Code",
        geom=geom_4326,
        id_nomenclature_type_site=list_nomenclature_id[0],
        types_site=list_nomenclature_id,
        id_sites_group=site_group_without_sites.id_sites_group,
    )

    post_data = dict()
    post_data["dataComplement"] = {}
    for type_site_dic in mock_db_type_site:
        copy_dic = type_site_dic.copy()
        copy_dic.pop("label")
        post_data["dataComplement"][type_site_dic["label"]] = copy_dic

    post_data["dataComplement"]["types_site"] = list_nomenclature_id
    post_data["properties"] = MonitoringSitesSchema().dump(site_to_post_with_types)
    post_data["properties"]["types_site"] = list_nomenclature_id

    for type_site in mock_db_type_site:
        specific_config = type_site["config"]["specific"]
        for key_specific in specific_config:
            if key_specific in specific_dic.keys():
                post_data["properties"][key_specific] = specific_dic[key_specific]
            else:
                post_data["properties"][key_specific] = None

    return post_data
