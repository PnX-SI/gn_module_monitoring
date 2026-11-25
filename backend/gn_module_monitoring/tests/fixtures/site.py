import datetime
import pytest
import json

from sqlalchemy import select

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from geonature.utils.env import db

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema


def add_to_observers_list(*users):
    """
    Inscrit les utilisateurs dans la liste d'observateurs `obsocctax` (liste par défaut des modules) : les
    observateurs d'un site (id_inventor, id_digitiser) sont validés par le store contre cette liste.
    """
    from pypnusershub.db.models import UserList

    observers_list = db.session.scalar(select(UserList).where(UserList.code_liste == "obsocctax"))
    with db.session.begin_nested():
        for user in users:
            if user not in observers_list.users:
                observers_list.users.append(user)


@pytest.fixture()
def sites(users, types_site, site_group_with_sites):
    add_to_observers_list(users["user"], users["admin_user"])
    user = users["user"]
    admin_user = users["admin_user"]
    geom_point = from_shape(Point(43, 24), srid=4326)
    sites = {}
    for i, key in enumerate(types_site.keys()):
        sites[key] = TMonitoringSites(
            id_inventor=user.id_role,
            id_digitiser=user.id_role,
            base_site_name=f"Site{i}user",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_point,
            types_site=[types_site[key]],
            id_sites_group=site_group_with_sites.id_sites_group,
            first_use_date=datetime.date(2025, 1, 1),
            data={
                "profondeur_grotte": 42.8,
                "owner_name": "Robert",
                "meteo": 2,
                "roost_type": "grotte",
            },
        )

    for i, key in enumerate(types_site.keys()):
        sites["admin_user_" + key] = TMonitoringSites(
            id_inventor=admin_user.id_role,
            id_digitiser=admin_user.id_role,
            base_site_name=f"Site{i} admin_user",
            base_site_description=f"Description{i}",
            base_site_code=f"Code{i}",
            geom=geom_point,
            types_site=[types_site[key]],
            id_sites_group=site_group_with_sites.id_sites_group,
        )

    # Add a special site that has no type
    sites["no-type"] = TMonitoringSites(
        id_inventor=user.id_role,
        id_digitiser=user.id_role,
        base_site_name="no-type",
        base_site_description="Description-no-type",
        base_site_code="Code-no-type",
        geom=geom_point,
        types_site=[],
        id_sites_group=site_group_with_sites.id_sites_group,
    )

    with db.session.begin_nested():
        db.session.add_all(sites.values())
    return sites


@pytest.fixture()
def sites_with_data_typeutils(users, types_site_type_utils, site_group_with_sites):
    user = users["user"]
    geom_point = from_shape(Point(43, 24), srid=4326)
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
            geom=geom_point,
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
    add_to_observers_list(users["user"])
    user = users["user"]
    list_nomenclature_id = []
    # roost_type : champ spécifique obligatoire des types de site de test
    specific_dic = {
        "owner_name": "Propriétaire",
        "threat": "Menaces",
        "owner_tel": "0609090909",
        "roost_type": "grotte",
    }
    schema_type_site = BibTypeSiteSchema()
    mock_db_type_site = [schema_type_site.dump(type) for type in types_site.values()]
    types_site = [type["id_nomenclature_type_site"] for type in mock_db_type_site]

    for type in mock_db_type_site:
        list_nomenclature_id.append(type["id_nomenclature_type_site"])

    post_data = {
        "id_inventor": user.id_role,
        "id_digitiser": user.id_role,
        "base_site_name": "New Site",
        "base_site_description": "New Description",
        "base_site_code": "New Code",
        "geom": {"type": "Point", "coordinates": [43, 24]},
        "types_site": list_nomenclature_id,
        "id_sites_group": site_group_without_sites.id_sites_group,
        **specific_dic,
    }

    return post_data
