import pytest
import json

from sqlalchemy import select

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from geonature.utils.env import db

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema


@pytest.fixture()
def sites(monitorings_users, types_site, site_group_with_sites):
    user = monitorings_users["user"]
    geom_4326 = from_shape(Point(43, 24), srid=4326)
    sites = {}
    for i, key in enumerate(types_site.keys()):
        sites[key] = TMonitoringSites(
            id_inventor=user.id_role,
            id_digitiser=user.id_role,
            base_site_name=f"Site{i}user",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_4326,
            types_site=[types_site[key]],
            id_sites_group=site_group_with_sites.id_sites_group,
        )

    user = monitorings_users["admin_user"]
    for i, key in enumerate(types_site.keys()):
        sites["admin_user_" + key] = TMonitoringSites(
            id_inventor=user.id_role,
            id_digitiser=user.id_role,
            base_site_name=f"Site{i} admin_user",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_4326,
            types_site=[types_site[key]],
            id_sites_group=site_group_with_sites.id_sites_group,
        )

    # Add a special site that has no type
    sites["no-type"] = TMonitoringSites(
        id_inventor=monitorings_users["user"].id_role,
        id_digitiser=monitorings_users["user"].id_role,
        base_site_name="no-type",
        base_site_description="Description-no-type",
        base_site_code="Code-no-type",
        geom=geom_4326,
        types_site=[],
        id_sites_group=site_group_with_sites.id_sites_group,
    )

    with db.session.begin_nested():
        db.session.add_all(sites.values())
    return sites


@pytest.fixture()
def sites_with_data_typeutils(users, types_site_type_utils, site_group_with_sites):
    user = users["user"]
    geom_4326 = from_shape(Point(43, 24), srid=4326)
    sites = {}
    nomenclature_sex = db.session.scalars(
        select(TNomenclatures)
        .where(TNomenclatures.nomenclature_type.has(BibNomenclaturesTypes.mnemonique == "SEXE"))
        .where(TNomenclatures.cd_nomenclature == "2")
        .limit(1)
    ).first()
    for i, key in enumerate(types_site_type_utils.keys()):
        sites[key] = TMonitoringSites(
            id_inventor=user.id_role,
            id_digitiser=user.id_role,
            base_site_name=f"Site{i}",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_4326,
            types_site=[types_site_type_utils[key]],
            id_sites_group=site_group_with_sites.id_sites_group,
            data={
                "observers3": user.id_role,
                "cd_nom_test": 212,
                "id_nomenclature_sex": nomenclature_sex.id_nomenclature,
                "multiple_observers3": [user.id_role],
                "multiple_cd_nom_test": [212, 99165],
                "multiple_id_nomenclature_sex": [nomenclature_sex.id_nomenclature],
            },
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
        base_site_name="New Site",
        base_site_description="New Description",
        base_site_code="New Code",
        geom=geom_4326,
        # types_site=list_nomenclature_id,
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

    post_data["geometry"] = json.loads(post_data["properties"].pop("geometry"))

    post_data["type"] = "Feature"
    post_data["properties"]["types_site"] = list_nomenclature_id

    for type_site in mock_db_type_site:
        specific_config = type_site["config"]["specific"]
        for key_specific in specific_config:
            if key_specific in specific_dic.keys():
                post_data["properties"][key_specific] = specific_dic[key_specific]
            else:
                post_data["properties"][key_specific] = None

    return post_data
