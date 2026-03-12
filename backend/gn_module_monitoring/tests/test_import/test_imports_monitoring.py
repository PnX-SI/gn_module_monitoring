from pathlib import Path

import pytest
import sqlalchemy as sa
from apptax.taxonomie.models import BibListes
from flask import current_app, g
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import TBaseSites, TBaseVisits, TObservations
from geonature.core.imports.models import Destination
from geonature.tests.imports.utils import assert_import_errors
from geonature.utils.env import db
from pypnusershub.db.models import UserList

from gn_module_monitoring.command.cmd import cmd_add_update_import_on_protocole
from gn_module_monitoring.monitoring.models import TMonitoringModules

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
    return {
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


@pytest.fixture()
def autogenerate():
    return False


@pytest.fixture(scope="function")
def override_in_importfile(
    import_datasets,
):
    return {
        "@FORBIDDEN_DATASET_UUID@": str(import_datasets["admin"].unique_dataset_id),
        "@INACTIVE_DATASET_UUID@": str(import_datasets["user--inactive"].unique_dataset_id),
        "@DATASET_NOT_FOUND@": "03905a03-c7fa-4642-b143-5005fa805377",
        "@VALID_DATASET_UUID@": str(import_datasets["user"].unique_dataset_id),
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
