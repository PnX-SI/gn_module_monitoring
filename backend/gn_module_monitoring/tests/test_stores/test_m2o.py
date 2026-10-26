import pytest
import sqlalchemy as sa
from marshmallow import ValidationError
from pypnusershub.db.models import User
from pypnnomenclature.models import TNomenclatures

from geonature.utils.env import db
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.stores.relationships.m2o import (
    NomenclatureStore,
    SiteStore,
    UserStore,
)
from gn_module_monitoring.tools.stores.relationships.utils import (
    get_nomenclature,
    get_nomenclature_type,
)
from gn_module_monitoring.tools.utils import schema_context


def make_store(store_cls, config, field_name="my_field"):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        return store_cls(config)


@pytest.mark.usefixtures("temporary_transaction")
class TestUserStore:
    def test_single_user_wire_type(self):
        assert make_store(UserStore, {}).get_wire_type() is int

    def test_multiple_users_wire_type(self):
        assert make_store(UserStore, {"multiple": True}).get_wire_type() == list[int]

    def test_accepts_existing_user_id(self, users):
        field = make_store(UserStore, {}).to_field()
        id_role = users["user"].id_role
        assert field.deserialize(id_role) == id_role

    def test_rejects_unknown_user_id(self):
        field = make_store(UserStore, {}).to_field()
        unknown = db.session.scalar(sa.select(sa.func.max(User.id_role))) + 1000
        with pytest.raises(ValidationError):
            field.deserialize(unknown)

    def test_rejects_non_integer(self):
        field = make_store(UserStore, {}).to_field()
        with pytest.raises(ValidationError):
            field.deserialize("Bob")


@pytest.mark.usefixtures("temporary_transaction")
class TestSiteStore:
    def test_wire_type_is_int(self):
        assert make_store(SiteStore, {}).get_wire_type() is int

    def test_rejects_unknown_site_id(self):
        field = make_store(SiteStore, {}).to_field()
        with pytest.raises(ValidationError):
            field.deserialize(-1)

    def test_none_is_accepted_when_optional(self):
        field = make_store(SiteStore, {}).to_field()
        assert field.deserialize(None) is None

    def test_serialize_pk_returns_value(self):
        field = make_store(SiteStore, {}).to_field()
        assert field._serialize(42, "site", None) == 42


@pytest.mark.usefixtures("temporary_transaction", "install_module_test")
class TestNomenclatureStore:
    @pytest.fixture(autouse=True)
    def clear_nomenclature_cache(self):
        # Les fonctions de recherche de nomenclature sont mises en cache : évite de réutiliser
        # des instances d’une transaction de test précédente
        get_nomenclature_type.cache_clear()
        get_nomenclature.cache_clear()
        yield
        get_nomenclature_type.cache_clear()
        get_nomenclature.cache_clear()

    @pytest.fixture
    def meteo_nomenclature(self):
        return db.session.execute(
            sa.select(TNomenclatures).where(TNomenclatures.cd_nomenclature == "METEO_B")
        ).scalar_one()

    def test_nomenclature_type_from_code_nomenclature_type(self):
        store = make_store(
            NomenclatureStore,
            {"code_nomenclature_type": "TEST_METEO"},
        )
        assert store["nomenclature_type"].mnemonique == "TEST_METEO"

    def test_nomenclature_type_from_nomenclature_type(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store["nomenclature_type"].mnemonique == "TEST_METEO"

    def test_default_storage_cols(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store["storage_cols"] == ["id_nomenclature", "cd_nomenclature", "label_default"]

    def test_unknown_nomenclature_type_is_rejected(self):
        with pytest.raises(ValidationError):
            make_store(NomenclatureStore, {"nomenclature_type": "UNKNOWN_TYPE_XYZ"})

    def test_unknown_cd_nomenclature_is_rejected(self):
        with pytest.raises(ValidationError):
            make_store(
                NomenclatureStore,
                {"nomenclature_type": "TEST_METEO", "cd_nomenclatures": ["ZZZ"]},
            )

    def test_storage_cols_must_contain_pk(self):
        with pytest.raises(ValidationError):
            make_store(
                NomenclatureStore,
                {"nomenclature_type": "TEST_METEO", "storage_cols": ["cd_nomenclature"]},
            )

    def test_wire_type_is_int(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store.get_wire_type() is int

    def test_dump_config_exposes_type_mnemonique(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store.dump_config()["code_nomenclature_type"] == "TEST_METEO"

    def test_accepts_existing_nomenclature_id(self, meteo_nomenclature):
        field = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"}).to_field()
        assert field.deserialize(meteo_nomenclature.id_nomenclature) == (
            meteo_nomenclature.id_nomenclature
        )

    def test_serialize_pk_returns_value(self):
        field = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"}).to_field()
        assert field._serialize(7, "meteo", None) == 7

    def test_serialize_storage_cols_dict_returns_pk(self):
        field = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"}).to_field()
        value = {"id_nomenclature": 7, "cd_nomenclature": "B", "label_default": "Beau"}
        assert field._serialize(value, "meteo", None) == 7
