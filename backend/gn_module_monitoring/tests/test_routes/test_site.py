from datetime import date

import pytest
from flask import url_for
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from pypnusershub.tests.utils import set_logged_user_cookie

from geonature.utils.env import db
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema
from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringModules,
)
from gn_module_monitoring.tests.fixtures.generic import *


@pytest.mark.usefixtures("client_class")
class TestSite:
    def test_get_type_site_by_id(self, types_site):
        for type_site in types_site.values():
            r = self.client.get(
                url_for(
                    "monitorings.get_type_site_by_id",
                    id_type_site=type_site.id_nomenclature_type_site,
                )
            )
            assert r.json["id_nomenclature_type_site"] == type_site.id_nomenclature_type_site

    def test_get_types_site(self, types_site):
        schema = BibTypeSiteSchema()

        r = self.client.get(url_for("monitorings.get_types_site"))

        assert r.json["count"] >= len(types_site)
        assert all([schema.dump(cat) in r.json["items"] for cat in types_site.values()])

    def test_get_sites(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        schema = MonitoringSitesSchema()

        r = self.client.get(url_for("monitorings.get_sites"))
        assert r.status_code == 200
        assert r.json["count"] >= len(sites)

        sites_response = r.json["items"]
        for s in sites_response:
            s.pop("cruved")

        assert any([schema.dump(site) in sites_response for site in sites.values()])

    def test_get_sites_order_by(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        ids_sites = [s.id_base_site for k, s in sites.items()]
        r = self.client.get(url_for("monitorings.get_sites", sort="id_base_site", sort_dir="desc"))
        assert r.json["count"] >= len(sites)
        assert r.json["items"][0]["id_base_site"] == max(ids_sites)
        r = self.client.get(url_for("monitorings.get_sites", sort="id_base_site", sort_dir="asc"))
        assert r.json["items"][0]["id_base_site"] == min(ids_sites)

        r = self.client.get(url_for("monitorings.get_sites", sort="id_inventor", sort_dir="desc"))
        assert r.json["count"] >= len(sites)
        assert r.json["items"][0]["inventor"] == [users["user"].nom_complet]

        r = self.client.get(url_for("monitorings.get_sites", sort="id_inventor", sort_dir="asc"))

        assert r.json["count"] >= len(sites)
        assert r.json["items"][0]["inventor"] == [users["admin_user"].nom_complet]

    def test_get_sites_order_by_unknown_field(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for("monitorings.get_sites", sort="unknown_field", sort_dir="desc")
        )
        assert r.json["count"] >= len(sites)

        r = self.client.get(
            url_for("monitorings.get_sites", sort="id_base_site", sort_dir="unknown_sort")
        )
        assert r.json["count"] >= len(sites)

    def test_get_sites_filters(self, sites, visits, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(url_for("monitorings.get_sites", last_visit="2025"))
        assert r.json["count"] >= len(sites)

        r = self.client.get(url_for("monitorings.get_sites", last_visit="2026"))
        assert r.json["count"] == 0

        # Test filters with inventor name
        resp = self.client.get(url_for("monitorings.get_sites", id_inventor="Bob"))
        nb_results = resp.json["count"]
        assert nb_results >= 3

        # Test filters  with inventor name with order by
        resp = self.client.get(
            url_for(
                "monitorings.get_sites",
                id_inventor="Bob",
                sort="id_inventor",
                sort_dir="desc",
            )
        )
        assert nb_results == resp.json["count"]

        # Test get all sites with order by
        resp = self.client.get(
            url_for(
                "monitorings.get_sites",
                sort="id_base_site",
                sort_dir="desc",
            )
        )
        assert resp.json["count"] == len(sites)

    def test_get_sites_filters_types_site(self, sites, types_site, users):
        set_logged_user_cookie(self.client, users["admin_user"])

        r = self.client.get(
            url_for(
                "monitorings.get_sites",
                types_site=types_site["Test_Grotte"].id_nomenclature_type_site,
            )
        )
        assert r.json["count"] == 2

        r = self.client.get(url_for("monitorings.get_sites", types_site="Test_Grotte"))
        assert r.json["count"] == 2

        r = self.client.get(url_for("monitorings.get_sites", types_site_label="Test_Grotte"))
        assert r.json["count"] == 2

    def test_get_sites_limit(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        limit = 2

        r = self.client.get(url_for("monitorings.get_sites", limit=limit))

        assert len(r.json["items"]) == limit

    def test_get_sites_base_site_name(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]
        base_site_name = site.base_site_name

        r = self.client.get(url_for("monitorings.get_sites", base_site_name=base_site_name))

        assert len(r.json["items"]) == 1
        assert r.json["items"][0]["base_site_name"] == base_site_name

    def test_get_sites_id_base_site(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]
        id_base_site = site.id_base_site

        r = self.client.get(url_for("monitorings.get_sites", id_base_site=id_base_site))

        assert len(r.json["items"]) == 1
        assert r.json["items"][0]["id_base_site"] == id_base_site

    def test_get_sites_by_id(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]
        id_base_site = site.id_base_site

        r = self.client.get(
            url_for("monitorings.get_site_by_id", id=id_base_site, object_type="site")
        )

        assert r.json["id_base_site"] == id_base_site

    def test_get_all_site_geometries(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(url_for("monitorings.get_all_site_geometries"))

        json_resp = r.json
        features = json_resp.get("features")
        sites_values = list(sites.values())
        assert r.content_type == "application/json"
        assert json_resp.get("type") == "FeatureCollection"
        assert len(features) >= len(sites_values)
        for site in sites_values:
            id_ = [
                obj["properties"]
                for obj in features
                if obj["properties"]["base_site_name"] == site.base_site_name
            ][0]["id_base_site"]
            assert id_ == site.id_base_site

    def test_get_all_site_geometries_filter_site_group_without_sites(
        self, sites, site_group_without_sites, users
    ):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                id_sites_group=site_group_without_sites.id_sites_group,
            )
        )
        json_resp = r.json
        features = json_resp.get("features")

        assert r.status_code == 200
        assert features is None

    def test_get_all_site_geometries_filter_site_group(self, sites, site_group_with_sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                id_sites_group=site_group_with_sites.id_sites_group,
            )
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) > 0

    def test_get_all_site_geometries_filters(
        self,
        sites,
        users,
    ):
        set_logged_user_cookie(self.client, users["admin_user"])
        nb_site_with_user_user = 3
        # Test with user's id
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                id_inventor=users["user"].id_role,
            )
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) == nb_site_with_user_user

        # Test with user's name
        # Utilisation de l'utilisateur admin car plus discrimant lors d'une recherche ilike
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                id_inventor=users["admin_user"].nom_role,
            )
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) == len(sites) - nb_site_with_user_user

    def test_get_all_site_geometries_filter_utils(self, sites_with_data_typeutils, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        # types_site = [s.types_site[0].id_nomenclature_type_site for s in sites_with_data_typeutils]
        types_site = [s for s in sites_with_data_typeutils]
        id_nomenclature_type_site = (
            sites_with_data_typeutils[types_site[0]].types_site[0].id_nomenclature_type_site
        )
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                types_site=id_nomenclature_type_site,
                cd_nom_test="Sonneur",
                observers3=users["user"].nom_complet,
                id_nomenclature_sex="Femelle",
            )
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) == 1
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                types_site=id_nomenclature_type_site,
                cd_nom_test="Sonneur",
                observers3=users["user"].nom_complet,
                id_nomenclature_sex="Femelle",
                multiple_cd_nom_test="Sonneur",
                multiple_observers3=users["user"].nom_complet,
                multiple_id_nomenclature_sex="Femelle",
            )
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) == 1

    def test_get_all_site_geometries_filter_type_sites(self, sites_with_data_typeutils, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        # types_site = [s.types_site[0].id_nomenclature_type_site for s in sites_with_data_typeutils]
        types_site = [s for s in sites_with_data_typeutils]
        id_nomenclature_type_site = (
            sites_with_data_typeutils[types_site[0]].types_site[0].id_nomenclature_type_site
        )
        r = self.client.get(
            url_for("monitorings.get_all_site_geometries", types_site=id_nomenclature_type_site)
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) == 1
        nom_type_site = list(sites_with_data_typeutils.keys())[0]
        r = self.client.get(
            url_for(
                "monitorings.get_all_site_geometries",
                types_site=nom_type_site,
            )
        )
        json_resp = r.json
        features = json_resp.get("features")
        assert r.status_code == 200
        assert len(features) == 1

    # def test_get_module_by_id_base_site(self, sites, monitoring_module, users):

    #     set_logged_user_cookie(self.client, users["admin_user"])
    #     site = list(sites.values())[0]
    #     id_base_site = site.id_base_site

    #     r = self.client.get(
    #         url_for("monitorings.get_module_by_id_base_site", id_base_site=id_base_site)
    #     )
    #     expected_modules = {monitoring_module.id_module}
    #     current_modules = {module["id_module"] for module in r.json}
    #     assert expected_modules.issubset(current_modules)

    def test_get_module_by_id_base_site_no_type_module(
        self, sites, monitoring_module_wo_types_site, users
    ):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]
        id_base_site = site.id_base_site

        r = self.client.get(
            url_for("monitorings.get_module_by_id_base_site", id_base_site=id_base_site)
        )

        expected_absent_modules = {monitoring_module_wo_types_site.id_module}
        current_modules = {module["id_module"] for module in r.json}
        assert expected_absent_modules.isdisjoint(current_modules)

    def test_get_module_by_id_base_site_no_type_site(self, sites, monitoring_module, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        id_base_site = sites["no-type"].id_base_site

        r = self.client.get(
            url_for("monitorings.get_module_by_id_base_site", id_base_site=id_base_site)
        )
        expected_modules = {monitoring_module.id_module}
        current_modules = {module["id_module"] for module in r.json}
        assert expected_modules.isdisjoint(current_modules)

    def test_get_module_by_id_base_site_permission_filtering(
        self, sites, modules_with_and_without_permission, users
    ):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]

        r = self.client.get(
            url_for("monitorings.get_module_by_id_base_site", id_base_site=site.id_base_site)
        )
        assert r.status_code == 200, f"Erreur HTTP {r.status_code} : {r.data}"
        ids = {m["id_module"] for m in r.json}
        assert modules_with_and_without_permission["with_perm"].id_module in ids
        assert modules_with_and_without_permission["without_perm"].id_module not in ids

    def test_get_module_by_id_base_site_filtered_by_site_type_and_permissions(
        self, sites, modules_with_permissions_and_different_types
    ):
        admin_user = modules_with_permissions_and_different_types["admin_user"]
        modules = modules_with_permissions_and_different_types["modules"]

        set_logged_user_cookie(self.client, admin_user)

        for label, module in modules.items():
            site = sites.get(label)
            assert site, f"Aucun site trouvé pour le type {label}"

            r = self.client.get(
                url_for("monitorings.get_module_by_id_base_site", id_base_site=site.id_base_site)
            )

            assert r.status_code == 200, f"Échec HTTP pour site {label}"
            ids = {m["id_module"] for m in r.json}

            # ✅ Seul le module de ce type doit être présent
            assert module.id_module in ids, f"{label} doit être présent"
            for other_label, other_module in modules.items():
                if other_label != label:
                    assert (
                        other_module.id_module not in ids
                    ), f"{other_label} ne doit pas apparaître pour site {label}"

    def test_get_module_sites(self, monitoring_module, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        module_code = "TEST"
        r = self.client.get(url_for("monitorings.get_module_sites", module_code=module_code))
        assert r.json["module_code"] == module_code

    def test_get_types_site_by_label(self, types_site, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        schema = BibTypeSiteSchema()
        mock_db_type_site = [schema.dump(type) for type in types_site.values()]
        string_contains = "e"
        string_missing = "a"

        query_string = {
            "limit": 100,
            "page": 1,
            "sort_label": "label_fr",
            "sort_dir": "asc",
            "label_fr": string_contains,
        }
        r = self.client.get(
            url_for("monitorings.get_types_site_by_label"), query_string=query_string
        )
        assert all([string_contains in item["label"] for item in r.json["items"]])
        assert all([type in r.json["items"] for type in mock_db_type_site])

        query_string["label_fr"] = string_missing
        r = self.client.get(
            url_for("monitorings.get_types_site_by_label"), query_string=query_string
        )
        assert all([type not in r.json["items"] for type in mock_db_type_site])

    def test_post_sites(
        self, site_to_post_with_types, types_site, site_group_without_sites, users
    ):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.post(
            url_for("monitorings.post_sites"), data=site_to_post_with_types
        )
        assert response.status_code == 201

        obj_created = response.json
        res = db.get_or_404(TMonitoringSites, obj_created["id"])
        assert (
            res.as_dict()["base_site_name"]
            == site_to_post_with_types["properties"]["base_site_name"]
        )

        assert set(res.types_site) == set([ts for k, ts in types_site.items()])

    def test_delete_site(self, sites, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        site = list(sites.values())[0]
        id_base_site = site.id_base_site
        r = self.client.delete(url_for("monitorings.delete_site", _id=id_base_site))

        assert r.json["success"] == "Item is successfully deleted"
        with pytest.raises(Exception) as e:
            db.get_or_404(TMonitoringSites, id_base_site)
        assert "404 Not Found" in str(e.value)


# @pytest.fixture()
# def add_site(test_module_user, types_site, site_group_with_sites):
#
#     def _add_site(**kwargs):
#         _add_site.counter += 1
#         i = _add_site.counter
#         user = test_module_user
#         geom_4326 = from_shape(Point(43, 24), srid=4326)
#         args = {
#             "id_inventor": user.id_role,
#             "id_digitiser": user.id_role,
#             "base_site_name": f"Site{i}",
#             "base_site_description": f"Description{i}",
#             "base_site_code": f"Code{i}",
#             "geom": geom_4326,
#             "types_site": list(types_site.values()),
#             "id_sites_group": site_group_with_sites.id_sites_group,
#         }
#         args.update(**kwargs)
#         site = TMonitoringSites(**args)
#         with db.session.begin_nested():
#             db.session.add(site)
#         return site
#
#     _add_site.counter = 0
#
#     return _add_site


# TODO: ajouter tests sur filtre par permissions
@pytest.mark.usefixtures("client_class", "temporary_transaction", "install_module_test")
class TestSiteWithModule:

    def test_get_module_sites(
        self,
        test_module_user,
        types_site,
        add_site,
    ):
        set_logged_user_cookie(self.client, test_module_user)
        sites = []
        for type in types_site.values():
            sites.append(
                add_site(
                    types_site=[type],
                    data={
                        "profondeur_grotte": 42.8,
                        "owner_name": "Robert",
                        "meteo": 2,
                    },
                )
            )
        add_site(types_site=[], base_site_name="no-type")

        response = self.client.get(url_for("monitorings.get_sites", module_code="test"))

        assert response.status_code == 200
        assert (
            response.json["count"] == 2
        )  # Les 2 sites avec des types de site qui matchent le module test
        sites_response = response.json["items"]
        assert len(sites_response) == 2
        sites_repr_ids = [s["id_base_site"] for s in sites_response]
        for site in sites:
            assert site.id_base_site in sites_repr_ids

        site_repr = sites_response[0]

        # Attribut spécifique du site est présent
        assert site_repr.get("profondeur_grotte") == 42.8

        # Attribut spécifique du type de site est présent
        assert site_repr.get("owner_name") == "Robert"

        # ID retourné pour attribut spécifique du site
        assert site_repr.get("meteo") == 2

    def test_get_module_sites_with_filter_on_generic_attribute(self, test_module_user, add_site):
        set_logged_user_cookie(self.client, test_module_user)
        filter_params = {"base_site_name": "gr"}
        add_site(base_site_name="Grotte")  # Sera retourné avec le filtre
        add_site(
            base_site_name="Grange", types_site=[]
        )  # Non lié au module, ne devrait pas être retourné

        response = self.client.get(
            url_for("monitorings.get_sites", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == 1
        site_repr = sites_response[0]
        assert site_repr["base_site_name"] == "Grotte"

    def test_get_module_sites_with_filter_on_site_specific_attribute(
        self, test_module_user, add_site
    ):
        set_logged_user_cookie(self.client, test_module_user)
        filter_params = {"profondeur_grotte": "48"}
        site_1 = add_site(data={"profondeur_grotte": 48.7})  # Sera retourné avec le filtre
        site_2 = add_site(data={"profondeur_grotte": 480})  # Sera retourné avec le filtre
        add_site(
            data={"profondeur_grotte": 48}, types_site=[]
        )  # Non lié au module, ne devrait pas être retourné

        response = self.client.get(
            url_for("monitorings.get_sites", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == 2
        sites_ids = [s["id_base_site"] for s in sites_response]
        assert site_1.id_base_site in sites_ids
        assert site_2.id_base_site in sites_ids

    def test_get_module_sites_with_filter_on_site_type_specific_attribute(
        self, test_module_user, add_site
    ):
        set_logged_user_cookie(self.client, test_module_user)
        filter_params = {"place_name": "to"}
        site_1 = add_site(data={"place_name": "Toulouse"})  # Sera retourné avec le filtre
        add_site(data={"place_name": "Marseille"})  # Pas de correspondance
        add_site(
            data={"place_name": "Toulon"}, types_site=[]
        )  # Non lié au module, ne devrait pas être retourné

        response = self.client.get(
            url_for("monitorings.get_sites", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == 1
        sites_ids = [s["id_base_site"] for s in sites_response]
        assert site_1.id_base_site in sites_ids

    def test_get_module_sites_with_filter_on_site_specific_nomenclature_attribute(
        self, test_module_user, add_site
    ):
        set_logged_user_cookie(self.client, test_module_user)
        beau = self._get_meteo_value("Beau")
        mauvais = self._get_meteo_value("Mauvais")
        filter_params = {"meteo": "mauv"}
        site = add_site(data={"meteo": mauvais.id_nomenclature})  # match
        add_site(data={"meteo": beau.id_nomenclature})  # no match
        add_site()  # empty "meteo" => no match

        response = self.client.get(
            url_for("monitorings.get_sites", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == 1
        sites_ids = [s["id_base_site"] for s in sites_response]
        assert site.id_base_site in sites_ids

    def test_get_module_sites_with_filter_on_site_type_specific_nomenclature_attribute(
        self, test_module_user, add_site
    ):
        set_logged_user_cookie(self.client, test_module_user)
        beau = self._get_meteo_value("Beau")
        mauvais = self._get_meteo_value("Mauvais")
        filter_params = {"meteo_gite": "mauv"}
        site = add_site(data={"meteo_gite": mauvais.id_nomenclature})  # match
        add_site(data={"meteo_gite": beau.id_nomenclature})  # no match
        add_site()  # empty "meteo" => no match

        response = self.client.get(
            url_for("monitorings.get_sites", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == 1
        sites_ids = [s["id_base_site"] for s in sites_response]
        assert site.id_base_site in sites_ids

    def test_get_module_sites_with_filter_on_site_nb_visits(
        self, test_module_user, add_site, datasets
    ):
        set_logged_user_cookie(self.client, test_module_user)
        filter_params = {"nb_visits": 2}
        dataset = datasets["own_dataset"]
        site1 = add_site()  # 1 visit : no match
        self.add_visit(site1, dataset)
        site2 = add_site()  # 2 visits : match
        for _ in range(2):
            self.add_visit(site2, dataset)
        site3 = add_site()  # 2 visits : match
        for _ in range(2):
            self.add_visit(site3, dataset)
        site4 = add_site()  # 3 visits : no match
        for _ in range(3):
            self.add_visit(site4, dataset)

        response = self.client.get(
            url_for("monitorings.get_sites", module_code="test", **filter_params)
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == 2
        sites_repr_ids = [s["id_base_site"] for s in sites_response]
        assert site2.id_base_site in sites_repr_ids
        assert site3.id_base_site in sites_repr_ids

    @pytest.mark.parametrize(
        "page,dir,expected_names",
        [
            (1, "asc", ["abri", "arbre"]),
            (2, "asc", ["garage", "grange"]),
            (3, "asc", ["grotte"]),
            (1, "desc", ["grotte", "grange"]),
            (2, "desc", ["garage", "arbre"]),
            (3, "desc", ["abri"]),
        ],
    )
    def test_get_module_sites_ordering_by_generic_property(
        self, test_module_user, add_site, page, dir, expected_names
    ):
        set_logged_user_cookie(self.client, test_module_user)
        add_site(base_site_name="arbre")
        add_site(base_site_name="grange")
        add_site(base_site_name="abri")
        add_site(base_site_name="grotte")
        add_site(base_site_name="garage")

        response = self.client.get(
            url_for(
                "monitorings.get_sites",
                module_code="test",
                sort="base_site_name",
                sort_dir=dir,
                page=page,
                limit=2,
            )
        )

        assert response.status_code == 200
        sites_response = response.json["items"]
        assert len(sites_response) == len(expected_names)
        for i, name in enumerate(expected_names):
            assert sites_response[i]["base_site_name"] == name

    @pytest.mark.parametrize(
        "page,dir,expected_names",
        [
            (1, "asc", ["Alain", "Alice"]),
            (2, "asc", ["Robert", "Roger"]),
            (3, "asc", ["Sarah"]),
            (1, "desc", ["Sarah", "Roger"]),
            (2, "desc", ["Robert", "Alice"]),
            (3, "desc", ["Alain"]),
        ],
    )
    def test_get_module_sites_ordering_by_text_specific_property(
        self, test_module_user, add_site, page, dir, expected_names
    ):
        set_logged_user_cookie(self.client, test_module_user)
        add_site(data={"contact_name": "Robert"})
        add_site(data={"contact_name": "Alice"})
        add_site(data={"contact_name": "Roger"})
        add_site(data={"contact_name": "Alain"})
        add_site(data={"contact_name": "Sarah"})

        response = self.client.get(
            url_for(
                "monitorings.get_sites",
                module_code="test",
                sort="contact_name",
                sort_dir=dir,
                page=page,
                limit=2,
            )
        )
        assert response.status_code == 200
        sites_response = response.json["items"]
        names_response = [s["contact_name"] for s in sites_response]
        assert names_response == expected_names

    @pytest.mark.parametrize(
        "page,dir,expected_names",
        [
            (1, "asc", ["Alain", "Alice"]),
            (2, "asc", ["Robert", "Roger"]),
            (3, "asc", ["Sarah"]),
            (1, "desc", ["Sarah", "Roger"]),
            (2, "desc", ["Robert", "Alice"]),
            (3, "desc", ["Alain"]),
        ],
    )
    def test_get_module_sites_ordering_by_text_specific_property(
        self, test_module_user, add_site, page, dir, expected_names
    ):
        set_logged_user_cookie(self.client, test_module_user)
        add_site(data={"contact_name": "Robert"})
        add_site(data={"contact_name": "Alice"})
        add_site(data={"contact_name": "Roger"})
        add_site(data={"contact_name": "Alain"})
        add_site(data={"contact_name": "Sarah"})

        response = self.client.get(
            url_for(
                "monitorings.get_sites",
                module_code="test",
                sort="contact_name",
                sort_dir=dir,
                page=page,
                limit=2,
            )
        )
        assert response.status_code == 200
        sites_response = response.json["items"]
        names_response = [s["contact_name"] for s in sites_response]
        assert names_response == expected_names

    @pytest.mark.parametrize(
        "page,dir,expected_meteo_values",
        [
            (1, "asc", ["Beau", "Beau"]),
            (2, "asc", ["Mauvais", "Nuageux"]),
            (3, "asc", ["Nuageux"]),
            (1, "desc", ["Nuageux", "Nuageux"]),
            (2, "desc", ["Mauvais", "Beau"]),
            (3, "desc", ["Beau"]),
        ],
    )
    def test_get_module_sites_ordering_by_nomenclature_specific_property(
        self, test_module_user, add_site, page, dir, expected_meteo_values
    ):
        set_logged_user_cookie(self.client, test_module_user)
        meteo_map = {
            "Beau": self._get_meteo_value("Beau"),
            "Mauvais": self._get_meteo_value("Mauvais"),
            "Nuageux": self._get_meteo_value("Nuageux"),
        }
        add_site(data={"meteo": meteo_map["Nuageux"].id_nomenclature})
        add_site(data={"meteo": meteo_map["Beau"].id_nomenclature})
        add_site(data={"meteo": meteo_map["Nuageux"].id_nomenclature})
        add_site(data={"meteo": meteo_map["Mauvais"].id_nomenclature})
        add_site(data={"meteo": meteo_map["Beau"].id_nomenclature})

        response = self.client.get(
            url_for(
                "monitorings.get_sites",
                module_code="test",
                sort="meteo",
                sort_dir=dir,
                page=page,
                limit=2,
            )
        )
        assert response.status_code == 200
        sites_response = response.json["items"]
        sites_meteos = [s["meteo"] for s in sites_response]
        expected_meteo_ids = [
            self._get_meteo_value(m).id_nomenclature for m in expected_meteo_values
        ]
        assert sites_meteos == expected_meteo_ids

    @staticmethod
    def add_visit(site, dataset):
        module = db.session.execute(
            select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
        ).scalar()
        args = {
            "id_base_site": site.id_base_site,
            "id_module": module.id_module,
            "visit_date_min": date.today(),
            "visit_date_max": date.today(),
            "id_dataset": dataset.id_dataset,
        }
        visit = TMonitoringVisits(**args)
        with db.session.begin_nested():
            db.session.add(visit)
        return visit

    @staticmethod
    def _get_meteo_value(mnemonique):
        return db.session.execute(
            select(TNomenclatures)
            .join(BibNomenclaturesTypes)
            .where(BibNomenclaturesTypes.mnemonique == "TEST_METEO")
            .where(TNomenclatures.mnemonique == mnemonique)
        ).scalar()

    @pytest.fixture
    def add_site(self, test_module_user, types_site, site_group_with_sites):

        def _add_site(**kwargs):
            _add_site.counter += 1
            i = _add_site.counter
            user = test_module_user
            geom_4326 = from_shape(Point(43, 24), srid=4326)
            args = {
                "id_inventor": user.id_role,
                "id_digitiser": user.id_role,
                "base_site_name": f"Site{i}",
                "base_site_description": f"Description{i}",
                "base_site_code": f"Code{i}",
                "geom": geom_4326,
                "types_site": list(types_site.values()),
                "id_sites_group": site_group_with_sites.id_sites_group,
            }
            args.update(**kwargs)
            site = TMonitoringSites(**args)
            with db.session.begin_nested():
                db.session.add(site)
            return site

        _add_site.counter = 0

        return _add_site
