import copy
import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from apptax.taxonomie.models import BibListes
from flask import current_app, g, url_for
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from werkzeug.datastructures import Headers
from werkzeug.exceptions import Conflict

from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import TBaseSites, TBaseVisits, TObservations
from geonature.core.imports.checks.errors import ImportCodeError
from geonature.core.imports.models import BibFields, Destination, Entity, TImports
from geonature.core.imports.utils import insert_import_data_in_transient_table
from geonature.tests.imports.utils import assert_import_errors
from geonature.tests.utils import logged_user, set_logged_user, unset_logged_user
from geonature.utils.env import db
from pypnusershub.db.models import UserList

from gn_module_monitoring.command.cmd import cmd_add_update_import_on_protocole
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringSitesGroups,
)
from gn_module_monitoring.command.imports.protocol import update_protocol

occhab = pytest.importorskip("gn_module_occhab")


from gn_module_occhab.models import OccurenceHabitat, Station

# ######################################################################################
# Fixtures -- override default values
# ######################################################################################


@pytest.fixture()
def install_test_module_with_import(install_module_test):
    module_test = db.session.execute(
        sa.select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one_or_none()

    with db.session.begin_nested():
        module_test.id_list_taxonomy = db.session.scalar(sa.select(BibListes.id_liste).limit(1))
        module_test.id_list_observer = db.session.scalar(sa.select(UserList.id_liste).limit(1))
        module_test.taxonomy_display_field_name = "nom_vern,lb_nom"
        db.session.add(module_test)
    runner = current_app.test_cli_runner()
    result = runner.invoke(cmd_add_update_import_on_protocole, ["test"])

    assert result.exit_code == 0

    site_fields = db.session.scalars(
        sa.select(BibFields).where(
            BibFields.id_destination
            == sa.select(Destination.id_destination).where(
                Destination.module.has(TModules.module_code == "test")
            )
        )
    ).all()

    assert set(
        [
            "s__roost_type",
            "s__meteo",
            "s__place_name",
            "s__owner_name",
            "s__owner_adress",
            "s__owner_tel",
            "s__owner_mail",
            "s__opening",
            "s__threat",
            "s__recommandation",
            "s__meteo_gite",
        ]
    ).issubset(set([f.name_field for f in site_fields]))


@pytest.fixture()
def import_destination(install_test_module_with_import, module_code):
    return Destination.query.filter(
        Destination.module.has(TModules.module_code == module_code)
    ).one()


@pytest.fixture()
def default_import_destination(app, default_destination, import_destination):
    g.default_destination = import_destination
    yield
    del g.default_destination


@pytest.fixture()
def tests_path():
    return Path(__file__).parent


@pytest.fixture(scope="class")
def testfiles_folder():  # provide with a default value - should bve overriden
    return ""


@pytest.fixture(scope="class")
def module_code():
    return "test"


@pytest.fixture(scope="class")
def fieldmapping_preset_name():
    return None


@pytest.fixture()
def fieldmapping(
    import_file_name,
    autogenerate,
    import_dataset,
    fieldmapping_unique_dataset_id,
    fieldmapping_preset_name,
    preset_fieldmapping,
    types_site,
):
    # Colonnes propres aux groupes de sites.
    # Pas de mapping "modules" : cor_sites_group_module est rempli automatiquement
    # avec le module de la destination d'import.
    sites_group_mapping = {
        "uuid_sites_group": {"column_src": "uuid_sites_group"},
        "id_sites_group_origin": {"column_src": "id_sites_group_origin"},
        "g__sites_group_code": {"column_src": "g__sites_group_code"},
        "g__sites_group_name": {"column_src": "g__sites_group_name"},
        "g__group_specific": {"column_src": "g__group_specific"},
        "g__altitude_min": {"column_src": "g__altitude_min"},
        "g__altitude_max": {"column_src": "g__altitude_max"},
        "g__geom": {"column_src": "g__geom"},
    }
    # Import de groupes de sites seuls : aucun champ site/visite/observation mappé
    if import_file_name == "only_sites_groups.csv":
        return sites_group_mapping
    mapping = {
        "uuid_base_site": {"column_src": "uuid_base_site"},
        "s__base_site": {"column_src": "s__base_site"},
        "s__id_inventor": {"constant_value": {"id_role": 3}},
        "s__base_site_code": {"column_src": "s__base_site_code"},
        "s__base_site_name": {"column_src": "s__base_site_name"},
        "s__base_site_description": {"column_src": "s__base_site_description"},
        "s__first_use_date": {"column_src": "s__first_use_date"},
        "s__meteo": {"column_src": "s__meteo"},
        "s__profondeur_grotte": {"column_src": "s__profondeur_grotte"},
        "s__contact_name": {"column_src": "s__contact_name"},
        "s__types_site": {
            "constant_value": [list(types_site.values())[0].id_nomenclature_type_site]
        },
        "s__roost_type": {"column_src": "s__roost_type"},
        "y": {"column_src": "y"},
        "x": {"column_src": "x"},
        "uuid_base_visit": {"column_src": "uuid_base_visit"},
        "unique_dataset_id": {"column_src": "id_dataset"},
        "v__visit_date_min": {"column_src": "v__visit_date_min"},
        "v__visit_date_max": {"column_src": "v__visit_date_max"},
        "v__meteo": {"column_src": "v__meteo"},
        "v__observers": {"column_src": "v__observers"},
        "uuid_observation": {"column_src": "uuid_observation"},
        "o__cd_nom": {"column_src": "o__cd_nom"},
        "o__comments": {"column_src": "o__comments"},
    }
    if "sites_group" in import_file_name:
        mapping.update(sites_group_mapping)
    return mapping


@pytest.fixture()
def autogenerate():
    return False


@pytest.fixture(scope="function")
def override_in_importfile(
    import_datasets,
    site_group_without_sites,
):
    return {
        "@FORBIDDEN_DATASET_UUID@": str(import_datasets["admin"].unique_dataset_id),
        "@INACTIVE_DATASET_UUID@": str(import_datasets["user--inactive"].unique_dataset_id),
        "@DATASET_NOT_FOUND@": "03905a03-c7fa-4642-b143-5005fa805377",
        "@VALID_DATASET_UUID@": str(import_datasets["user"].unique_dataset_id),
        "@EXISTING_GROUP_UUID@": str(site_group_without_sites.uuid_sites_group),
    }


@pytest.fixture(scope="class")
def fieldmapping_preset_name():
    return None


@pytest.fixture(scope="class")
def contentmapping_preset_name():
    return None


@pytest.fixture(scope="function")
def add_in_contentmapping():
    """Nomenclature label to cd_nomenclature mappings"""
    return {
        "TEST_METEO": {
            "Beau": "METEO_B",
            "Nuageux": "METEO_N",
            "Mauvais": "METEO_M",
        }
    }


@pytest.fixture()
def no_default_uuid(monkeypatch):
    monkeypatch.setitem(current_app.config["IMPORT"], "DEFAULT_GENERATE_MISSING_UUID", False)


@pytest.fixture()
def sites_group_mandatory_config(monkeypatch):
    """Simule un protocole où le groupe de sites est obligatoire : "site" n'est pas
    au premier niveau du tree (cf. isSitesGroupMandatory dans check_transient_data)."""
    from gn_module_monitoring.config import repositories

    original_get_config = repositories.get_config

    def get_config_without_first_level_site(module_code=None, force=False):
        # deepcopy pour ne pas muter la config mise en cache dans current_app.config
        config = copy.deepcopy(original_get_config(module_code, force))
        if module_code == "test":
            config["tree"]["module"].pop("site", None)
        return config

    monkeypatch.setattr(repositories, "get_config", get_config_without_first_level_site)


def run_import(
    client,
    user,
    tests_path,
    import_file_name,
    override_in_importfile,
    fieldmapping,
    contentmapping,
    observers_mapping,
):
    """Rejoue la chaîne complète d'import (mêmes étapes que les fixtures
    uploaded_import -> ... -> imported_import) pour un second import dans un même test."""
    set_logged_user(client, user)
    with open(tests_path / "files" / import_file_name, "rb") as f:
        r = client.post(
            url_for("import.upload_file"),
            data={"file": (f, import_file_name)},
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
    assert r.status_code == 200, r.data
    imprt = db.session.get(TImports, r.get_json()["id_import"])
    for before, after in override_in_importfile.items():
        imprt.source_file = imprt.source_file.replace(
            before.encode("ascii"),
            after.encode("ascii"),
        )
    db.session.flush()
    r = client.post(
        url_for("import.decode_file", import_id=imprt.id_import),
        data={"encoding": "utf-8", "format": "csv", "srid": 4326, "separator": ";"},
    )
    assert r.status_code == 200, r.data
    db.session.refresh(imprt)
    with db.session.begin_nested():
        imprt.fieldmapping = fieldmapping
        imprt.source_count = insert_import_data_in_transient_table(imprt)
        imprt.loaded = True
        imprt.contentmapping = contentmapping
        imprt.observermapping = observers_mapping
    r = client.post(url_for("import.prepare_import", import_id=imprt.id_import))
    assert r.status_code == 200, r.data
    r = client.post(url_for("import.import_valid_data", import_id=imprt.id_import))
    assert r.status_code == 200, r.data
    unset_logged_user(client)
    db.session.refresh(imprt)
    return imprt


@pytest.mark.usefixtures(
    "client_class",
    "temporary_transaction",
    "celery_eager",
    "install_test_module_with_import",
    "import_destination",
    "default_import_destination",
    "module_code",
    "fieldmapping_preset_name",
    "testfiles_folder",
    "contentmapping_preset_name",
)
class TestImportMonitoring:
    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "valid_hierarchy_comma.csv", None)],
    )
    def test_import_valid_file(self, datasets, imported_import):
        assert_import_errors(
            imported_import,
            set([]),
        )
        assert imported_import.statistics == {
            "site_count": 3,
            "visit_count": 4,
            "observation_count": 6,
            "taxa_count": 6,
            "import_count": 13,
            "nb_line_valid": 6,
        }
        assert (
            db.session.scalar(
                sa.select(sa.func.count()).where(TBaseSites.id_import == imported_import.id_import)
            )
            == imported_import.statistics["site_count"]
        )
        assert (
            db.session.scalar(
                sa.select(sa.func.count()).where(
                    TBaseVisits.id_import == imported_import.id_import
                )
            )
            == imported_import.statistics["visit_count"]
        )
        assert (
            db.session.scalar(
                sa.select(sa.func.count(sa.distinct(TObservations.cd_nom))).where(
                    TObservations.id_import == imported_import.id_import
                )
            )
            == imported_import.statistics["observation_count"]
        )

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "valid_sites_groups.csv", None)],
    )
    def test_import_valid_sites_groups(self, datasets, imported_import):
        assert_import_errors(
            imported_import,
            set([]),
        )

        assert imported_import.statistics == {
            "sites_group_count": 2,
            "site_count": 3,
            "visit_count": 4,
            "observation_count": 6,
            "taxa_count": 6,
            "import_count": 15,  # 2 groupes + 3 sites + 4 visites + 6 observations
            "nb_line_valid": 6,
        }

        groups = db.session.scalars(
            sa.select(TMonitoringSitesGroups).where(
                TMonitoringSitesGroups.id_import == imported_import.id_import
            )
        ).all()
        # Deux groupes de sites importés
        assert len(groups) == 2
        assert {group.sites_group_code for group in groups} == {"GA", "GB"}

        groups_by_code = {group.sites_group_code: group for group in groups}
        group_a = groups_by_code["GA"]
        group_b = groups_by_code["GB"]

        # Les sites sont rattachés à leur groupe parent
        assert len(group_a.sites) == 2
        assert len(group_b.sites) == 1

        # GA : rattachement par UUID fourni -> l'UUID du CSV est conservé
        assert str(group_a.uuid_sites_group) == "11111111-1111-1111-1111-111111111111"
        # GB : rattachement par id_sites_group_origin (aucun UUID fourni) -> UUID généré
        assert group_b.uuid_sites_group is not None

        for group in groups:
            # Rattachement au module (cor_sites_group_module)
            assert "test" in [module.module_code for module in group.modules]
            # Géométrie du groupe importée telle quelle depuis le fichier
            assert group.geom is not None

        # Altitudes importées telles quelles (check_altitudes ne valide que min <= max)
        assert (group_a.altitude_min, group_a.altitude_max) == (100, 500)
        assert (group_b.altitude_min, group_b.altitude_max) == (200, 600)

        # Champ spécifique du groupe stocké dans data (clé sans le préfixe g__),
        # à parité avec les champs spécifiques de site/visite/observation
        assert group_a.data["group_specific"] == "spec A"
        assert group_b.data["group_specific"] == "spec B"

        # Le polygone importé de chaque groupe englobe la géométrie de ses sites enfants
        # (cohérence des données du fichier, group.geom n'est pas une bbox calculée)
        for group in groups:
            for site in group.sites:
                assert db.session.scalar(sa.select(sa.func.ST_Covers(group.geom, site.geom)))

        # La bounding box de l'import (SitesGroupImportActions.compute_bounding_box)
        # fusionne l'emprise des groupes (GA+GB : x [6.0, 6.9], y [44.5, 44.9])
        # et celle des sites enfants (incluse ici dans celle des groupes)
        bbox = imported_import.destination.actions.compute_bounding_box(imported_import)
        assert json.loads(json.dumps(bbox)) == {
            "type": "Polygon",
            "coordinates": [
                [
                    [6.0, 44.9],
                    [6.0, 44.5],
                    [6.9, 44.5],
                    [6.9, 44.9],
                    [6.0, 44.9],
                ]
            ],
        }

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "only_sites_groups.csv", None)],
    )
    def test_import_only_sites_groups(self, datasets, imported_import):
        """Import d'un fichier ne contenant que des groupes de sites, sans aucun champ
        site/visite/observation mappé."""
        assert_import_errors(
            imported_import,
            set([]),
        )
        assert imported_import.statistics == {
            "sites_group_count": 2,
            "import_count": 2,
            "nb_line_valid": 2,
        }

        groups = db.session.scalars(
            sa.select(TMonitoringSitesGroups).where(
                TMonitoringSitesGroups.id_import == imported_import.id_import
            )
        ).all()
        assert len(groups) == 2
        groups_by_code = {group.sites_group_code: group for group in groups}
        assert set(groups_by_code) == {"GC1", "GC2"}
        # GC1 : UUID du fichier conservé ; GC2 : UUID généré via id_sites_group_origin
        assert (
            str(groups_by_code["GC1"].uuid_sites_group) == "12121212-1212-1212-1212-121212121212"
        )
        assert groups_by_code["GC2"].uuid_sites_group is not None
        for group in groups:
            assert "test" in [module.module_code for module in group.modules]
            assert group.geom is not None
            assert len(group.sites) == 0
        assert groups_by_code["GC1"].data["group_specific"] == "spec C1"
        assert groups_by_code["GC2"].data["group_specific"] == "spec C2"

        # Sans site enfant, la bounding box de l'import est celle des groupes seuls
        bbox = imported_import.destination.actions.compute_bounding_box(imported_import)
        assert bbox is not None and bbox["type"] == "Polygon"
        xs = [x for x, y in bbox["coordinates"][0]]
        ys = [y for x, y in bbox["coordinates"][0]]
        assert (min(xs), max(xs), min(ys), max(ys)) == (6.0, 6.9, 44.5, 44.9)

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "invalid_sites_groups.csv", None)],
    )
    def test_import_sites_groups_errors(self, datasets, prepared_import):
        # Ligne 3 : altitude min > altitude max ; ligne 4 : WKT non parsable.
        # Le groupe en erreur invalide en cascade le site de la ligne, puis la
        # visite et l'observation (ERRONEOUS_PARENT_ENTITY).
        expected_errors = {
            (
                ImportCodeError.ALTI_MIN_SUP_ALTI_MAX,
                "sites_group",
                "g__altitude_min",
                frozenset({3}),
            ),
            (
                ImportCodeError.INVALID_WKT,
                "sites_group",
                "WKT",
                frozenset({4}),
            ),
            (
                ImportCodeError.ERRONEOUS_PARENT_ENTITY,
                "site",
                "",
                frozenset({3, 4}),
            ),
            (
                ImportCodeError.ERRONEOUS_PARENT_ENTITY,
                "visit",
                "",
                frozenset({3, 4}),
            ),
            (
                ImportCodeError.ERRONEOUS_PARENT_ENTITY,
                "observation",
                "",
                frozenset({3, 4}),
            ),
        }
        assert_import_errors(prepared_import, expected_errors)

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "invalid_sites_groups.csv", None)],
    )
    def test_preview_sites_groups_data(self, client, datasets, prepared_import):
        """La prévisualisation avant validation expose l'entité groupe de sites,
        ses colonnes mappées et ses comptages de lignes valides/invalides."""
        with logged_user(client, prepared_import.authors[0]):
            r = client.get(
                url_for("import.preview_valid_data", import_id=prepared_import.id_import)
            )
        assert r.status_code == 200, r.data
        entities = {e["entity"]["code"]: e for e in r.json["entities"]}
        assert set(entities) == {"sites_group", "site", "visit", "observation"}
        # Ligne 2 valide, lignes 3 et 4 invalides, pour chacune des quatre entités
        # (groupes en erreur puis cascade site -> visite -> observation)
        for code, entity_data in entities.items():
            assert entity_data["n_valid_data"] == 1, code
            assert entity_data["n_invalid_data"] == 2, code
        sites_group_columns = {c["prop"] for c in entities["sites_group"]["columns"]}
        assert {"g__sites_group_code", "g__sites_group_name"} <= sites_group_columns

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "incoherent_sites_groups.csv", None)],
    )
    def test_import_sites_groups_incoherent_uuid(self, datasets, prepared_import):
        """Même UUID de groupe sur deux lignes avec un contenu différent -> INCOHERENT_DATA.

        Le groupe devient non identifiable (validité None) : la référence de groupe des
        sites de ces lignes ne peut plus être résolue -> NO_PARENT_ENTITY sur les sites,
        puis cascade ERRONEOUS_PARENT_ENTITY sur leurs visites et observations.
        """
        expected_errors = {
            (
                ImportCodeError.INCOHERENT_DATA,
                "sites_group",
                "uuid_sites_group",
                frozenset({2, 3}),
            ),
            (
                ImportCodeError.NO_PARENT_ENTITY,
                "site",
                "uuid_sites_group",
                frozenset({2, 3}),
            ),
            (
                ImportCodeError.ERRONEOUS_PARENT_ENTITY,
                "visit",
                "",
                frozenset({2, 3}),
            ),
            (
                ImportCodeError.ERRONEOUS_PARENT_ENTITY,
                "observation",
                "",
                frozenset({2, 3}),
            ),
        }
        assert_import_errors(prepared_import, expected_errors)

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "no_parent_sites_groups.csv", None)],
    )
    def test_import_sites_groups_mandatory_no_parent(
        self, sites_group_mandatory_config, datasets, prepared_import
    ):
        """Groupe obligatoire (pas de "site" au 1er niveau du tree) : un site
        référençant un groupe inexistant (ligne 3, erreur portée par la référence
        fournie) ou sans aucun groupe (ligne 4) est rejeté."""
        expected_errors = {
            (
                ImportCodeError.NO_PARENT_ENTITY,
                "site",
                "uuid_sites_group",
                frozenset({3}),
            ),
            (
                ImportCodeError.NO_PARENT_ENTITY,
                "site",
                "id_sites_group",
                frozenset({4}),
            ),
        }
        assert_import_errors(prepared_import, expected_errors)

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "no_parent_sites_groups.csv", None)],
    )
    def test_import_sites_without_sites_group(self, datasets, imported_import):
        """Même fichier que test_import_sites_groups_mandatory_no_parent mais avec la
        config par défaut du module test ("site" au 1er niveau du tree -> groupe
        optionnel) : le site sans aucun groupe (ligne 4) est importé sans rattachement,
        mais le site référençant un groupe inexistant (ligne 3) reste rejeté — la
        référence fournie ne doit pas être silencieusement ignorée."""
        expected_errors = {
            (
                ImportCodeError.NO_PARENT_ENTITY,
                "site",
                "uuid_sites_group",
                frozenset({3}),
            ),
        }
        assert_import_errors(imported_import, expected_errors)
        assert imported_import.statistics == {
            "sites_group_count": 1,
            "site_count": 2,
            "visit_count": 1,
            "observation_count": 1,
            "taxa_count": 1,
            "import_count": 5,
            "nb_line_valid": 2,
        }
        sites = db.session.scalars(
            sa.select(TMonitoringSites).where(
                TMonitoringSites.id_import == imported_import.id_import
            )
        ).all()
        sites_by_code = {site.base_site_code: site for site in sites}
        assert set(sites_by_code) == {"site_np_01", "site_np_03"}
        group = db.session.execute(
            sa.select(TMonitoringSitesGroups).where(
                TMonitoringSitesGroups.id_import == imported_import.id_import
            )
        ).scalar_one()
        # Le site de la ligne 2 est rattaché au groupe défini sur sa ligne
        assert sites_by_code["site_np_01"].id_sites_group == group.id_sites_group
        # Le site sans aucune référence de groupe est importé sans rattachement
        assert sites_by_code["site_np_03"].id_sites_group is None

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "existing_sites_groups.csv", None)],
    )
    def test_import_site_attached_to_existing_sites_group(
        self, datasets, site_group_without_sites, imported_import
    ):
        """UUID de groupe déjà présent en base : le groupe du fichier est ignoré
        (SKIP_EXISTING_UUID, chemin skip=True) et le site est rattaché au groupe existant."""
        assert_import_errors(
            imported_import,
            {
                (
                    ImportCodeError.SKIP_EXISTING_UUID,
                    "sites_group",
                    "uuid_sites_group",
                    frozenset({2}),
                ),
            },
        )
        # Aucun groupe importé, le reste de la ligne est importé
        assert imported_import.statistics == {
            "site_count": 1,
            "visit_count": 1,
            "observation_count": 1,
            "taxa_count": 1,
            "import_count": 3,
            "nb_line_valid": 1,
        }
        site = db.session.execute(
            sa.select(TMonitoringSites).where(
                TMonitoringSites.id_import == imported_import.id_import
            )
        ).scalar_one()
        assert site.id_sites_group == site_group_without_sites.id_sites_group
        # Le groupe existant n'est pas modifié par l'import
        assert site_group_without_sites.id_import is None
        assert site_group_without_sites.sites_group_name == "Site_eolien"

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "valid_sites_groups.csv", None)],
    )
    def test_reimport_sites_groups_same_file(
        self,
        client,
        datasets,
        imported_import,
        tests_path,
        import_file_name,
        override_in_importfile,
        fieldmapping,
        contentmapping,
        observers_mapping,
    ):
        """Ré-import du même fichier : les entités identifiées par UUID sont ignorées
        (SKIP_EXISTING_UUID) et ne sont pas dupliquées."""
        second_import = run_import(
            client,
            imported_import.authors[0],
            tests_path,
            import_file_name,
            override_in_importfile,
            fieldmapping,
            contentmapping,
            observers_mapping,
        )
        expected_errors = {
            (
                ImportCodeError.SKIP_EXISTING_UUID,
                "sites_group",
                "uuid_sites_group",
                frozenset({2, 3, 4, 5, 6}),
            ),
            (
                ImportCodeError.SKIP_EXISTING_UUID,
                "site",
                "uuid_base_site",
                frozenset({2, 3, 4, 5, 6, 7}),
            ),
            (
                ImportCodeError.SKIP_EXISTING_UUID,
                "visit",
                "uuid_base_visit",
                frozenset({2, 3, 4, 5, 6, 7}),
            ),
            (
                ImportCodeError.SKIP_EXISTING_UUID,
                "observation",
                "uuid_observation",
                frozenset({2, 3, 4, 5, 6, 7}),
            ),
        }
        assert_import_errors(second_import, expected_errors)
        # GA (UUID fourni dans le fichier) n'est pas dupliqué, ni ses sites
        assert (
            db.session.scalar(
                sa.select(sa.func.count()).where(
                    TMonitoringSitesGroups.uuid_sites_group
                    == "11111111-1111-1111-1111-111111111111"
                )
            )
            == 1
        )
        assert (
            db.session.scalar(
                sa.select(sa.func.count()).where(
                    TBaseSites.uuid_base_site == "550e8400-e29b-41d4-a716-446655440002"
                )
            )
            == 1
        )
        # Comportement actuel : GB (identifié par id_sites_group_origin, sans UUID dans
        # le fichier) reçoit un UUID aléatoire à chaque import et est donc recréé,
        # sans site rattaché (son site, identifié par UUID, a été ignoré)
        gb_groups = db.session.scalars(
            sa.select(TMonitoringSitesGroups).where(
                TMonitoringSitesGroups.sites_group_code == "GB"
            )
        ).all()
        assert len(gb_groups) == 2
        second_gb = next(g for g in gb_groups if g.id_import == second_import.id_import)
        assert len(second_gb.sites) == 0
        assert second_import.statistics == {
            "sites_group_count": 1,
            "import_count": 1,
            "nb_line_valid": 1,
        }

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "valid_sites_groups.csv", None)],
    )
    def test_remove_imported_sites_groups(self, client, datasets, imported_import):
        id_import = imported_import.id_import
        with logged_user(client, imported_import.authors[0]):
            r = client.delete(url_for("import.delete_import", import_id=id_import))
        assert r.status_code == 200, r.data
        # Toutes les données de l'import sont supprimées, groupes de sites compris
        for model in (TMonitoringSitesGroups, TBaseSites, TBaseVisits, TObservations):
            assert (
                db.session.scalar(sa.select(sa.func.count()).where(model.id_import == id_import))
                == 0
            )

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "valid_sites_groups.csv", None)],
    )
    def test_remove_import_sites_group_with_manual_site(
        self, client, users, datasets, imported_import
    ):
        """La suppression de l'import est refusée (Conflict) si un site hors import
        est rattaché à un groupe de sites importé."""
        group = db.session.scalars(
            sa.select(TMonitoringSitesGroups)
            .where(TMonitoringSitesGroups.id_import == imported_import.id_import)
            .limit(1)
        ).first()
        site = TMonitoringSites(
            id_inventor=users["user"].id_role,
            id_digitiser=users["user"].id_role,
            base_site_name="Site manuel",
            base_site_code="SM1",
            base_site_description="Site créé hors import",
            geom=from_shape(Point(6.1, 44.6), srid=4326),
            types_site=[],
            id_sites_group=group.id_sites_group,
        )
        with db.session.begin_nested():
            db.session.add(site)
        with logged_user(client, imported_import.authors[0]):
            r = client.delete(url_for("import.delete_import", import_id=imported_import.id_import))
        assert r.status_code == Conflict.code, r.data
        assert str(group.id_sites_group) in r.json["description"]
        assert str(site.id_base_site) in r.json["description"]

    def test_update_module_label(self, import_destination, module_code):
        new_label = "test_change"
        module_data = {"module": {"module_label": new_label}}

        update_protocol(module_data, module_code, [], update_label_only=True)
        destination = db.session.execute(
            sa.select(Destination).where(
                Destination.module.has(TModules.module_code == module_code)
            )
        ).scalar_one()

        assert destination.label == f"Monitoring - {new_label}"

        entities = (
            db.session.execute(
                sa.select(Entity).where(Entity.id_destination == destination.id_destination)
            )
            .scalars()
            .all()
        )
        for entity in entities:
            assert entity.label == new_label
