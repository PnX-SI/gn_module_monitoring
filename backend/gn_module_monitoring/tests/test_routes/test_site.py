import pytest
from flask import url_for
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.monitoring.schemas import BibTypeSiteSchema, MonitoringSitesSchema
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
