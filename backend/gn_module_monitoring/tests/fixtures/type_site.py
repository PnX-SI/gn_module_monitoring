import json
import os

import pytest

from sqlalchemy import select

from geonature.utils.env import db
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures

from gn_module_monitoring.monitoring.models import BibTypeSite


def get_test_data(filename):
    folder_path = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(folder_path, "TestData")
    jsonfile = os.path.join(folder, filename)
    with open(jsonfile) as file:
        data = json.load(file)
    return data


@pytest.fixture
def nomenclature_types_site():
    mnemoniques = ("Test_Grotte", "Test_Mine")
    nomenclatures = []
    type_site = db.session.scalars(
        select(BibNomenclaturesTypes)
        .where(BibNomenclaturesTypes.mnemonique == "TYPE_SITE")
        .limit(1)
    ).first()
    for mnemo in mnemoniques:
        nomenclatures.append(
            TNomenclatures(
                id_type=type_site.id_type,
                cd_nomenclature=mnemo,
                label_default=mnemo,
                label_fr=mnemo,
                active=True,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(nomenclatures)
    return nomenclatures


@pytest.fixture
def types_site(nomenclature_types_site):
    config_type_site = get_test_data("config_type_site.json")
    types_site = {
        nomenc_type_site.label_default: BibTypeSite(
            id_nomenclature_type_site=nomenc_type_site.id_nomenclature, config=config_type_site
        )
        for nomenc_type_site in nomenclature_types_site
    }
    with db.session.begin_nested():
        db.session.add_all(types_site.values())
    return types_site
