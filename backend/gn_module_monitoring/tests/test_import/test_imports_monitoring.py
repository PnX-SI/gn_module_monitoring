from pathlib import Path

import pytest
import sqlalchemy as sa
from apptax.taxonomie.models import BibListes, cor_nom_liste
from flask import current_app, g
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import TBaseSites, TBaseVisits, TObservations
from geonature.core.imports.models import BibFields, Destination, Entity
from geonature.tests.imports.utils import assert_import_errors
from geonature.utils.env import db
from pypnusershub.db.models import UserList

from gn_module_monitoring.command.cmd import cmd_add_update_import_on_protocole
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.command.imports.protocol import update_protocol
import sqlalchemy as sa

occhab = pytest.importorskip("gn_module_occhab")


from gn_module_occhab.models import OccurenceHabitat, Station

WKT_IMPORT_FILES = ("valid_wkt.csv", "invalid_wkt.csv")

# ######################################################################################
# Fixtures -- override default values
# ######################################################################################


@pytest.fixture()
def install_test_module_with_import(install_module_test, datasets):
    module_test = db.session.execute(
        sa.select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one_or_none()

    with db.session.begin_nested():
        module_test.id_list_taxonomy = db.session.scalar(sa.select(BibListes.id_liste).limit(1))
        module_test.id_list_observer = db.session.scalar(sa.select(UserList.id_liste).limit(1))
        module_test.taxonomy_display_field_name = "nom_vern,lb_nom"
        module_test.datasets.append(datasets["orphan_dataset"])
        db.session.add(module_test)
    runner = current_app.test_cli_runner()
    result = runner.invoke(cmd_add_update_import_on_protocole, ["test"])

    assert result.exit_code == 0

    site_fields = db.session.scalars(
        sa.select(BibFields).where(
            BibFields.id_destination
            == sa.select(Destination.id_destination)
            .where(Destination.module.has(TModules.module_code == "test"))
            .scalar_subquery()
        )
    ).all()

    # Champs spécifiques des types de site (roost_type, owner_*, ...) : non fusionnés dans les bib_fields
    # du module tant que P1 (TASKS.md, « Champs spécifiques des types de site ») n'est pas fait.
    assert set(
        [
            "s__meteo",
            "s__base_site_code",
            "s__base_site_name",
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
        "y": {"column_src": "y"},
        "x": {"column_src": "x"},
        "uuid_base_visit": {"column_src": "uuid_base_visit"},
        "uuid_dataset": {"column_src": "id_dataset"},
        "v__visit_date_min": {"column_src": "v__visit_date_min"},
        "v__visit_date_max": {"column_src": "v__visit_date_max"},
        "v__meteo": {"column_src": "v__meteo"},
        "v__observers": {"column_src": "v__observers"},
        "uuid_observation": {"column_src": "uuid_observation"},
        "o__cd_nom": {"column_src": "o__cd_nom"},
        "o__comments": {"column_src": "o__comments"},
    }
    if import_file_name in WKT_IMPORT_FILES:
        # Géométrie en WKT (colonne source `s__geom`), x et y vides dans ces fichiers
        mapping["s__geom"] = {"column_src": "s__geom"}
    return mapping


@pytest.fixture()
def autogenerate():
    return False


@pytest.fixture(scope="function")
def override_in_importfile(
    import_datasets,
):
    module_test = db.session.execute(
        sa.select(TMonitoringModules).where(TMonitoringModules.module_code == "test")
    ).scalar_one_or_none()
    biblist_ = db.session.execute(
        sa.select(BibListes).where(BibListes.id_liste == module_test.id_list_taxonomy)
    ).scalar_one_or_none()
    with db.session.begin_nested():
        db.session.execute(
            sa.insert(cor_nom_liste).values(id_liste=biblist_.id_liste, cd_nom=655844)
        )

    return {
        "@FORBIDDEN_DATASET_UUID@": str(import_datasets["admin"].unique_dataset_id),
        "@INACTIVE_DATASET_UUID@": str(import_datasets["user--inactive"].unique_dataset_id),
        "@DATASET_NOT_FOUND@": "03905a03-c7fa-4642-b143-5005fa805377",
        "@VALID_DATASET_UUID@": str(import_datasets["user"].unique_dataset_id),
        "@VALID_CDNOM@": str(655844),
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
    def test_import_valid_file(self, imported_import):
        assert_import_errors(
            imported_import,
            set([]),
        )
        assert imported_import.statistics == {
            "import_count": 13,
            "site_count": 3,
            "visit_count": 4,
            "observation_count": 6,
            "taxa_count": 1,
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
                sa.select(sa.func.count(sa.distinct(TObservations.id_observation))).where(
                    TObservations.id_import == imported_import.id_import
                )
            )
            == imported_import.statistics["observation_count"]
        )
        assert (
            db.session.scalar(
                sa.select(sa.func.count(sa.distinct(TObservations.cd_nom))).where(
                    TObservations.id_import == imported_import.id_import
                )
            )
            == imported_import.statistics["taxa_count"]
        )

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "bad_cdnom.csv", None)],
    )
    def test_import_bad_cdnom_file(self, imported_import):
        errors = {
            (
                error.type.name,
                error.entity.code if error.entity else None,
                error.column,
                frozenset(error.rows or []),
            )
            for error in imported_import.errors
        }

        assert (
            "CD_NOM_NOT_FOUND",
            "observation",
            "o__cd_nom",
            frozenset({7, 8}),
        ) in errors

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


# Coordonnées des sites (uuid_base_site) des fichiers valid_hierarchy_comma.csv / valid_wkt.csv
SITE_POINTS_4326 = {
    "550e8400-e29b-41d4-a716-446655440002": (6.0531825, 44.5764805),
    "01b93717-ab9a-482c-a852-4e6f61ae2ac0": (6.762981626694984, 44.88250842566327),
    "4d514a15-6e9b-446a-aafe-1d22fad066e5": (6.834298469329738, 44.82957727096802),
}


def _import_sites_geometry(id_import):
    """Géométrie 4326 (X, Y, SRID), présence et SRID de geom_local des sites d'un import (SELECT)."""
    return {
        str(row.uuid_base_site): row
        for row in db.session.execute(
            sa.text(
                """
                SELECT uuid_base_site,
                       ST_SRID(geom) AS srid,
                       ST_X(geom) AS x,
                       ST_Y(geom) AS y,
                       geom_local IS NOT NULL AS has_geom_local,
                       ST_SRID(geom_local) AS srid_local
                FROM gn_monitoring.t_base_sites
                WHERE id_import = :id_import
                """
            ),
            {"id_import": id_import},
        ).all()
    }


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
class TestImportMonitoringGeometry:
    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [
            (False, "valid_hierarchy_comma.csv", None),  # x/y -> POINT construit
            (False, "valid_wkt.csv", None),  # WKT valide
        ],
    )
    def test_import_site_geometry(self, imported_import):
        """Import x/y ou WKT : géométrie 4326 du site = POINT(x y), geom_local renseignée (SRID local)."""
        assert_import_errors(imported_import, set([]))
        sites = _import_sites_geometry(imported_import.id_import)
        assert set(sites) == set(SITE_POINTS_4326)
        srid_local = db.session.scalar(
            sa.text(
                "SELECT Find_SRID('gn_monitoring', 't_base_sites', 'geom_local')"
            )
        )
        for uuid, (x, y) in SITE_POINTS_4326.items():
            site = sites[uuid]
            assert site.srid == 4326
            assert (site.x, site.y) == pytest.approx((x, y), abs=1e-9)
            assert site.has_geom_local
            assert site.srid_local == srid_local

    @pytest.mark.parametrize(
        "autogenerate, import_file_name,fieldmapping_preset_name",
        [(False, "invalid_wkt.csv", None)],
    )
    def test_import_invalid_wkt_rows_have_no_geometry(self, imported_import):
        """Un WKT 3D et un WKT non parsable sont rejetés : pas de site ni de geom_local pour ces lignes."""
        invalid_wkt_rows = set()
        for error in imported_import.errors:
            if error.type.name == "INVALID_WKT":
                assert error.column == "WKT"
                invalid_wkt_rows |= set(error.rows or [])
        # Numéros de ligne du fichier (en-tête = ligne 1) : lignes 5 et 6 (WKT 3D, site 01b93717)
        # et 7 (WKT non parsable, site 4d514a15)
        assert invalid_wkt_rows == {5, 6, 7}
        sites = _import_sites_geometry(imported_import.id_import)
        valid_uuid = "550e8400-e29b-41d4-a716-446655440002"
        assert set(sites) == {valid_uuid}
        assert (sites[valid_uuid].x, sites[valid_uuid].y) == pytest.approx(
            SITE_POINTS_4326[valid_uuid], abs=1e-9
        )
        assert sites[valid_uuid].has_geom_local
