import pytest
import sqlalchemy as sa
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures
from ref_geo.models import BibAreasTypes, LAreas

from geonature.utils.env import db


@pytest.fixture
def dep_area():
    return db.session.execute(
        sa.select(LAreas)
        .join(BibAreasTypes, LAreas.id_type == BibAreasTypes.id_type)
        .where(BibAreasTypes.type_code == "DEP", LAreas.area_code == "01")
    ).scalar_one()


@pytest.fixture
def other_type_area():
    # Seul le type DEP est présent en base de test : on crée une zone d'un autre type
    # (rollback avec la transaction du test)
    id_type = db.session.execute(
        sa.text(
            """
            INSERT INTO ref_geo.bib_areas_types
                (type_name, type_code, type_desc, ref_name, ref_version, num_version, size_hierarchy)
            VALUES ('Type de test', 'TEST_AREA_TYPE', 'Type de test', 'test', 1, '1', 1)
            RETURNING id_type
            """
        )
    ).scalar_one()
    id_area = db.session.execute(
        sa.text(
            """
            INSERT INTO ref_geo.l_areas (id_type, area_name, area_code, source, description, enable)
            VALUES (:id_type, 'Zone de test', 'TEST01', 'test', 'test', true)
            RETURNING id_area
            """
        ),
        {"id_type": id_type},
    ).scalar_one()
    return db.session.get(LAreas, id_area)


@pytest.fixture
def meteo_nomenclature():
    return db.session.execute(
        sa.select(TNomenclatures)
        .join(BibNomenclaturesTypes, TNomenclatures.id_type == BibNomenclaturesTypes.id_type)
        .where(
            BibNomenclaturesTypes.mnemonique == "TEST_METEO",
            TNomenclatures.cd_nomenclature == "METEO_B",
        )
    ).scalar_one()


@pytest.fixture
def other_type_nomenclature():
    # Une nomenclature qui n'appartient pas au type TEST_METEO
    return db.session.execute(
        sa.select(TNomenclatures)
        .join(BibNomenclaturesTypes, TNomenclatures.id_type == BibNomenclaturesTypes.id_type)
        .where(BibNomenclaturesTypes.mnemonique != "TEST_METEO")
        .limit(1)
    ).scalar_one()
