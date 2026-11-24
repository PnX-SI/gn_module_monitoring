import pytest
import sqlalchemy as sa
from marshmallow import ValidationError
from pypnusershub.db.models import User
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures

from geonature.utils.env import db
from gn_module_monitoring.modules import get_module
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.stores.relationships.m2o import (
    AreaStore,
    ModuleStore,
    NomenclatureStore,
    ObserverListStore,
    SiteStore,
    UserStore,
)
from gn_module_monitoring.tools.stores.relationships.utils import (
    get_nomenclature,
    get_nomenclature_type,
)
from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.tools.widgets.relationships import AreasWidget


def make_store(store_cls, config, field_name="my_field"):
    with schema_context(
        entity=ENTITY_MAP["site"], field_name=field_name, module=get_module("test")
    ):
        return store_cls(config)


@pytest.mark.usefixtures("temporary_transaction")
class TestUserStore:
    def test_single_user_api_type(self):
        assert make_store(UserStore, {}).get_api_type() is int

    def test_multiple_option_is_not_supported(self):
        with pytest.raises(ValidationError):
            make_store(UserStore, {"multiple": True})

    def test_accepts_existing_user_id(self, users):
        field = make_store(UserStore, {}).get_field()
        id_role = users["user"].id_role
        assert field.deserialize(id_role).id_role == id_role

    def test_rejects_unknown_user_id(self):
        field = make_store(UserStore, {}).get_field()
        unknown = db.session.scalar(sa.select(sa.func.max(User.id_role))) + 1000
        with pytest.raises(ValidationError):
            field.deserialize(unknown)

    def test_rejects_non_integer(self):
        field = make_store(UserStore, {}).get_field()
        with pytest.raises(ValidationError):
            field.deserialize("Bob")


@pytest.mark.usefixtures("temporary_transaction")
class TestModuleStore:
    def test_api_type_is_int(self):
        assert make_store(ModuleStore, {}).get_api_type() is int


class TestObserverListStore:
    def test_api_type_is_int(self):
        assert make_store(ObserverListStore, {}).get_api_type() is int


class TestSiteStore:
    def test_api_type_is_int(self):
        assert make_store(SiteStore, {}).get_api_type() is int

    def test_rejects_unknown_site_id(self):
        field = make_store(SiteStore, {}).get_field()
        with pytest.raises(ValidationError):
            field.deserialize(-1)

    def test_none_is_accepted_when_optional(self):
        field = make_store(SiteStore, {}).get_field()
        assert field.deserialize(None) is None

    def test_serialize_pk_returns_pk(self):
        field = make_store(SiteStore, {}).get_field()
        assert field._serialize(42, "site", None) == 42


@pytest.mark.usefixtures("temporary_transaction", "install_module_test_with_config")
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

    def test_nomenclature_type_from_code_nomenclature_type(self):
        store = make_store(
            NomenclatureStore,
            {"code_nomenclature_type": "TEST_METEO"},
        )
        assert store.nomenclature_type.mnemonique == "TEST_METEO"

    def test_nomenclature_type_from_nomenclature_type(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store.nomenclature_type.mnemonique == "TEST_METEO"

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

    def test_api_type_is_int(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store.get_api_type() is int

    def test_dump_config_exposes_type_mnemonique(self):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        assert store.dump_config()["code_nomenclature_type"] == "TEST_METEO"

    def test_accepts_existing_nomenclature_id(self, meteo_nomenclature):
        field = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"}).get_field()
        loaded = field.deserialize(meteo_nomenclature.id_nomenclature)
        assert loaded.id_nomenclature == meteo_nomenclature.id_nomenclature

    def test_serialize_pk_returns_pk(self):
        field = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"}).get_field()
        assert field._serialize(7, "meteo", None) == 7

    def test_storage_cols_dict_is_read_back_as_pk(self, meteo_nomenclature):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        stored = store.to_storage(meteo_nomenclature)
        assert stored["id_nomenclature"] == meteo_nomenclature.id_nomenclature
        assert store.from_storage(stored) == meteo_nomenclature.id_nomenclature

    def test_storage_col_is_read_back_as_pk(self, meteo_nomenclature):
        store = make_store(
            NomenclatureStore,
            {"nomenclature_type": "TEST_METEO", "storage_col": "cd_nomenclature"},
        )
        stored = store.to_storage(meteo_nomenclature)
        assert stored == meteo_nomenclature.cd_nomenclature
        assert store.from_storage(stored) == meteo_nomenclature.id_nomenclature

    def test_nomenclature_of_other_type_is_rejected(self, other_type_nomenclature):
        field = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"}).get_field()
        with pytest.raises(ValidationError):
            field.deserialize(other_type_nomenclature.id_nomenclature)

    def test_type_absent_from_db_rejects_any_nomenclature(self, meteo_nomenclature):
        store = make_store(NomenclatureStore, {"nomenclature_type": "TEST_METEO"})
        store.nomenclature_type = BibNomenclaturesTypes(mnemonique="TYPE_NON_INSTALLE")
        with pytest.raises(ValidationError):
            store.get_field().deserialize(meteo_nomenclature.id_nomenclature)


@pytest.mark.usefixtures("temporary_transaction", "install_module_test_with_config")
class TestAreaStore:
    def test_area_type_is_loaded(self):
        store = make_store(AreaStore, {"area_type_code": "DEP"})
        assert store.area_type.type_code == "DEP"

    def test_no_area_type_accepts_any_area(self, dep_area):
        store = make_store(AreaStore, {})
        assert store.area_type is None
        assert store.get_field().deserialize(dep_area.id_area).id_area == dep_area.id_area

    def test_unknown_area_type_is_rejected(self):
        with pytest.raises(ValidationError):
            make_store(AreaStore, {"area_type_code": "UNKNOWN_TYPE_XYZ"})

    def test_area_of_type_is_accepted(self, dep_area):
        field = make_store(AreaStore, {"area_type_code": "DEP"}).get_field()
        assert field.deserialize(dep_area.id_area).id_area == dep_area.id_area

    def test_area_of_other_type_is_rejected(self, other_type_area):
        field = make_store(AreaStore, {"area_type_code": "DEP"}).get_field()
        with pytest.raises(ValidationError):
            field.deserialize(other_type_area.id_area)

    def test_storage_col_is_resolved_within_area_type(self, dep_area):
        store = make_store(
            AreaStore,
            {"area_type_code": "DEP", "storage_col": "area_code"},
        )
        assert store.from_storage(dep_area.area_code) == dep_area.id_area

    def test_storage_col_ignores_areas_of_other_type(self, other_type_area):
        store = make_store(
            AreaStore,
            {"area_type_code": "DEP", "storage_col": "area_code"},
        )
        with pytest.raises(ValueError):
            store.from_storage(other_type_area.area_code)

    def test_widget_passes_area_type_code_to_single_store(self):
        with schema_context(
            entity=ENTITY_MAP["site"], field_name="my_field", module=get_module("test")
        ):
            store = AreasWidget({"multiple": False}).get_default_store({"area_type_code": "DEP"})
        assert isinstance(store, AreaStore)
        assert store.area_type.type_code == "DEP"

    def test_widget_passes_its_own_area_type_code_to_store(self):
        with schema_context(
            entity=ENTITY_MAP["site"], field_name="my_field", module=get_module("test")
        ):
            store = AreasWidget({"multiple": False, "area_type_code": "DEP"}).get_default_store()
        assert isinstance(store, AreaStore)
        assert store.area_type.type_code == "DEP"

    def test_widget_retro_compat_passes_area_type_code_to_store(self):
        with schema_context(
            entity=ENTITY_MAP["site"], field_name="my_field", module=get_module("test")
        ):
            store = AreasWidget(
                {"type_widget": "areas", "area_type_code": "DEP"}
            ).get_default_store()
        assert isinstance(store, AreaStore)
        assert store.area_type.type_code == "DEP"

    def test_widget_dump_config_exposes_type_codes(self):
        with schema_context(
            entity=ENTITY_MAP["site"], field_name="my_field", module=get_module("test")
        ):
            config = AreasWidget({"multiple": False, "area_type_code": "DEP"}).dump_config()
        assert config["type_codes"] == ["DEP"]

    def test_widget_dump_config_without_area_type_code_has_no_type_codes(self):
        with schema_context(
            entity=ENTITY_MAP["site"], field_name="my_field", module=get_module("test")
        ):
            config = AreasWidget({"multiple": False}).dump_config()
        assert "type_codes" not in config
