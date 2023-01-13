import pytest
from geonature.utils.env import db
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures

from gn_module_monitoring.monitoring.models import BibTypeSite


@pytest.fixture
def nomenclature_types_site():
    mnemoniques = ("Test_Grotte", "Test_Mine")
    nomenclatures = []
    type_site = BibNomenclaturesTypes.query.filter(
        BibNomenclaturesTypes.mnemonique == "TYPE_SITE"
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
    types_site = {
        nomenc_type_site.mnemonique: BibTypeSite(
            id_nomenclature=nomenc_type_site.id_nomenclature, config={}
        )
        for nomenc_type_site in nomenclature_types_site
    }
    with db.session.begin_nested():
        db.session.add_all(types_site.values())
    return types_site
