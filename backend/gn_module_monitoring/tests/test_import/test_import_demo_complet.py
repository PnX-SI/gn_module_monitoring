"""
Import du fichier `files/demo/demo_complet.csv` sur le protocole démo.

Le fichier couvre les entités importables (site, visite, observation) : des lignes valides, et des lignes
invalides qui déclenchent les erreurs d'import (format, référentiel, obligation, CEL, doublons, hiérarchie).
Chaque ligne du fichier porte un site, sa visite et son observation.

Les numéros de ligne sont ceux du fichier (en-tête = ligne 1). Les erreurs `ERRONEOUS_PARENT_ENTITY`,
`NO_PARENT_ENTITY`, `INCOHERENT_DATA` et les erreurs de même cause sur deux entités sont attendues.

Les deux derniers tests (`xfail`, stricts) documentent des contrôles qui ne sont pas encore appliqués.
"""

import uuid

import pytest
import sqlalchemy as sa
from apptax.taxonomie.models import BibListes, cor_nom_liste
from flask import current_app, g
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import TBaseSites, TObservations
from geonature.core.imports.models import Destination
from geonature.tests.imports.utils import assert_import_errors
from geonature.utils.env import db
from pypnusershub.db.models import UserList

from gn_module_monitoring.command.cmd import cmd_add_update_import_on_protocole
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.tests.fixtures.monitoring_modules import install_monitoring_module

MODULE_CODE = "demo"
TESTFILES_FOLDER = "demo"
IMPORT_FILE_NAME = "demo_complet.csv"

# Erreurs attendues : (type, entité, colonne, lignes)
EXPECTED_ERRORS = {
    ('ALTI_MIN_SUP_ALTI_MAX', 'site', 's__altitude_min', frozenset({10})),
    ('CD_NOM_NOT_FOUND', 'observation', 'o__cd_nom', frozenset({38})),
    ('CONDITIONAL_INVALID_DATA', 'observation', 'o__cd_nom', frozenset({38})),
    ('CD_NOM_NOT_FOUND', 'site', 's__demo_taxonomy', frozenset({20})),
    ('CLOSED_ACQUISITION_FRAMEWORK', 'visit', 'uuid_dataset', frozenset({34})),
    ('CONDITIONAL_INVALID_DATA', 'observation', "Contraintes de l'entité", frozenset({39})),
    ('CONDITIONAL_INVALID_DATA', 'site', "Contraintes de l'entité", frozenset({10, 21})),
    ('CONDITIONAL_INVALID_DATA', 'visit', "Contraintes de l'entité", frozenset({25})),
    ('CONDITIONAL_INVALID_DATA', 'observation', 'o__demo_count', frozenset({42})),
    ('CONDITIONAL_INVALID_DATA', 'site', 's__base_site_code', frozenset({9})),
    ('CONDITIONAL_INVALID_DATA', 'site', 's__cd_hab', frozenset({23})),
    ('CONDITIONAL_INVALID_DATA', 'site', 's__demo_date', frozenset({24})),
    ('CONDITIONAL_INVALID_DATA', 'site', 's__demo_taxonomy', frozenset({20})),
    ('CONDITIONAL_INVALID_DATA', 'visit', 'v__demo_visit_score', frozenset({29, 30})),
    ('DATASET_NOT_ACTIVE', 'visit', 'uuid_dataset', frozenset({32})),
    ('DATASET_NOT_AUTHORIZED', 'visit', 'uuid_dataset', frozenset({31})),
    ('DATASET_NOT_FOUND', 'visit', 'uuid_dataset', frozenset({33})),
    ('DATE_MIN_SUP_DATE_MAX', 'visit', 'v__visit_date_min', frozenset({25})),
    ('DATE_MIN_TOO_HIGH', 'visit', 'v__visit_date_min', frozenset({26})),
    ('CONDITIONAL_INVALID_DATA', 'visit', 'v__observers', frozenset({37})),
    ('ERRONEOUS_PARENT_ENTITY', 'observation', '', frozenset({8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37})),
    ('ERRONEOUS_PARENT_ENTITY', 'visit', '', frozenset({8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 22, 23, 24})),
    ('INCOHERENT_DATA', 'site', 'uuid_base_site', frozenset({13, 14})),
    ('INVALID_BOOL', 'site', 's__demo_bool', frozenset({18})),
    ('INVALID_DATE', 'site', 's__first_use_date', frozenset({11})),
    ('INVALID_INTEGER', 'observation', 'o__demo_count', frozenset({40})),
    ('INVALID_INTEGER', 'site', 's__demo_integer', frozenset({17})),
    ('INVALID_NOMENCLATURE', 'observation', 'o__demo_stade', frozenset({41})),
    ('INVALID_NOMENCLATURE', 'site', 's__demo_nomenclature', frozenset({19})),
    ('INVALID_NOMENCLATURE', 'visit', 'v__id_nomenclature_tech_collect_campanule', frozenset({28})),
    ('INVALID_NUMERIC', 'site', 's__x', frozenset({16})),
    ('INVALID_UUID', 'site', 'uuid_base_site', frozenset({12})),
    ('INVALID_UUID', 'visit', 'uuid_base_site', frozenset({12})),
    ('INVALID_UUID', 'observation', 'uuid_base_visit', frozenset({36})),
    ('INVALID_UUID', 'visit', 'uuid_base_visit', frozenset({36})),
    ('INVALID_UUID', 'observation', 'uuid_observation', frozenset({44})),
    ('MISSING_VALUE', 'observation', 'o__cd_nom', frozenset({43})),
    ('MISSING_VALUE', 'site', 's__base_site_code', frozenset({8})),
    ('MISSING_VALUE', 'site', 's__demo_select', frozenset({22})),
    ('MISSING_VALUE', 'site', 's__geom', frozenset({15, 16})),
    ('MISSING_VALUE', 'visit', 'v__demo_visit_type', frozenset({35})),
    ('MISSING_VALUE', 'visit', 'v__observers', frozenset({27})),
    ('NO_PARENT_ENTITY', 'visit', 'id_base_site', frozenset({13, 14})),
}

# Codes des sites des lignes valides (site A : ligne 2, site B : ligne 5, site C : ligne 6)
# Type de site du protocole démo (TYPE_SITE / DEMO, rattaché au module démo)
TYPE_SITE_DEMO = 74925

VALID_SITE_CODES = {"AB101", "CD202", "EF303"}
# Observation de la ligne valide 2 (uuid fourni)
VALID_OBSERVATION_UUID = "550e8400-e29b-41d4-a716-446655440501"


def observers_list(users):
    """Liste d'observateurs du module démo, qui contient les utilisateurs de test."""
    user_list = UserList(code_liste="demo_import", nom_liste="Observateurs (démo import)")
    user_list.users = list(users.values())
    with db.session.begin_nested():
        db.session.add(user_list)
    return user_list


@pytest.fixture()
def install_module_demo_with_import(users, datasets):
    # Pas de fixture `types_site` : les types de test ajouteraient leurs champs spécifiques au protocole démo.
    install_monitoring_module(MODULE_CODE, {}, users)
    module_demo = db.session.execute(
        sa.select(TMonitoringModules).where(TMonitoringModules.module_code == MODULE_CODE)
    ).scalar_one()
    with db.session.begin_nested():
        module_demo.id_list_taxonomy = db.session.scalar(sa.select(BibListes.id_liste).limit(1))
        module_demo.id_list_observer = observers_list(users).id_liste
        module_demo.taxonomy_display_field_name = "nom_vern,lb_nom"
        module_demo.datasets.append(datasets["orphan_dataset"])
        db.session.add(module_demo)
    # Le protocole installé en base peut être en retard sur la configuration : mise à jour
    # dans la transaction du test (annulée ensuite).
    result = current_app.test_cli_runner().invoke(
        cmd_add_update_import_on_protocole, [MODULE_CODE], input="yes\n"
    )
    assert result.exit_code == 0


@pytest.fixture()
def import_destination(install_module_demo_with_import, module_code):
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
    from pathlib import Path

    return Path(__file__).parent


@pytest.fixture(scope="class")
def testfiles_folder():
    return TESTFILES_FOLDER


@pytest.fixture(scope="class")
def module_code():
    return MODULE_CODE


@pytest.fixture(scope="class")
def fieldmapping_preset_name():
    return None


@pytest.fixture(scope="class")
def contentmapping_preset_name():
    return None


@pytest.fixture()
def import_file_name():
    return IMPORT_FILE_NAME


@pytest.fixture()
def autogenerate():
    return False


@pytest.fixture()
def add_in_contentmapping():
    return {}


@pytest.fixture()
def fieldmapping(tests_path, users):
    """
    Une colonne du fichier par champ importé (nom de colonne = nom d'import). Les champs constants
    (type de site, observateur du site) ne sont pas lus dans le fichier.
    """
    with open(tests_path / "files" / TESTFILES_FOLDER / IMPORT_FILE_NAME, encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n").split(";")
    mapping = {column: {"column_src": column} for column in header}
    mapping["s__types_site"] = {"constant_value": [TYPE_SITE_DEMO]}
    mapping["s__id_inventor"] = {"constant_value": {"id_role": users["user"].id_role}}
    return mapping


@pytest.fixture()
def observers_mapping(users):
    return {
        "obs_user": {"id_role": users["user"].id_role},
        "obs_user2": {"id_role": users["noright_user"].id_role},
    }


@pytest.fixture(scope="function")
def override_in_importfile(import_datasets):
    module_demo = db.session.execute(
        sa.select(TMonitoringModules).where(TMonitoringModules.module_code == MODULE_CODE)
    ).scalar_one()
    biblist = db.session.execute(
        sa.select(BibListes).where(BibListes.id_liste == module_demo.id_list_taxonomy)
    ).scalar_one()
    with db.session.begin_nested():
        db.session.execute(
            sa.insert(cor_nom_liste).values(id_liste=biblist.id_liste, cd_nom=655844)
        )
    return {
        "@FORBIDDEN_DATASET_UUID@": str(import_datasets["admin"].unique_dataset_id),
        "@INACTIVE_DATASET_UUID@": str(import_datasets["user--inactive"].unique_dataset_id),
        "@CLOSED_AF_DATASET_UUID@": str(import_datasets["user--closed-af"].unique_dataset_id),
        "@DATASET_NOT_FOUND@": "03905a03-c7fa-4642-b143-5005fa805377",
        "@VALID_DATASET_UUID@": str(import_datasets["user"].unique_dataset_id),
        "@VALID_CDNOM@": str(655844),
    }


@pytest.mark.usefixtures(
    "client_class",
    "temporary_transaction",
    "celery_eager",
    "install_module_demo_with_import",
    "import_destination",
    "default_import_destination",
    "module_code",
    "fieldmapping_preset_name",
    "testfiles_folder",
    "contentmapping_preset_name",
)
class TestImportDemoComplet:
    def test_import_demo_complet_errors(self, imported_import):
        assert_import_errors(imported_import, EXPECTED_ERRORS)

    def test_import_demo_complet_valid_rows_are_imported(self, imported_import):
        codes = set(
            db.session.scalars(
                sa.select(TBaseSites.base_site_code).where(
                    TBaseSites.id_import == imported_import.id_import
                )
            ).all()
        )
        assert codes == VALID_SITE_CODES
        observations = db.session.scalars(
            sa.select(TObservations).where(
                TObservations.uuid_observation == uuid.UUID(VALID_OBSERVATION_UUID)
            )
        ).all()
        assert len(observations) == 1
        assert observations[0].id_import == imported_import.id_import

    def test_unknown_observer_is_reported(self, imported_import):
        assert any(
            error.column == "v__observers" and 37 in (error.rows or [])
            for error in imported_import.errors
        )

    @pytest.mark.xfail(
        strict=True,
        reason="Deux observations de même uuid : la ligne 47 est invalidée sans erreur",
    )
    def test_duplicate_observation_uuid_is_reported(self, imported_import):
        assert any(
            error.type.name == "DUPLICATE_UUID" and {45, 46} <= set(error.rows or [])
            for error in imported_import.errors
        )
