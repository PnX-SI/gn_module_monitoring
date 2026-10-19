import pytest
import sqlalchemy as sa
from marshmallow import ValidationError

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.tools.stores.relationships.m2m import (
    AreasStore,
    NomenclaturesStore,
    TypesSiteStore,
)
from gn_module_monitoring.tools.stores.relationships.utils import get_nomenclature_type
from gn_module_monitoring.tools.utils import schema_context


def make_store(store_cls, config, field_name="my_field"):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        return store_cls(config)


@pytest.fixture
def types_site_relationship():
    return sa.inspect(TMonitoringSites).relationships["types_site"]


@pytest.mark.usefixtures("temporary_transaction")
class TestTypesSiteStore:
    def test_wire_type_is_list_of_int(self):
        assert make_store(TypesSiteStore, {}, field_name="types_site").get_wire_type() == list[int]

    def test_is_suitable_for_types_site_relationship(self, types_site_relationship):
        assert TypesSiteStore.is_suitable_for_relationship(types_site_relationship)

    def test_is_not_suitable_for_other_model(self, types_site_relationship):
        assert not AreasStore.is_suitable_for_relationship(types_site_relationship)

    def test_is_not_suitable_without_relationship(self):
        assert not TypesSiteStore.is_suitable_for_relationship(None)

    def test_native_relationship_is_accepted(self):
        store = make_store(TypesSiteStore, {}, field_name="types_site")
        assert store.native_attr is not None

    def test_column_attr_is_rejected_when_strict(self, app, monkeypatch):
        monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", True)
        with pytest.raises(ValidationError):
            make_store(TypesSiteStore, {}, field_name="base_site_name")

    def test_column_attr_only_warns_when_not_strict(self, app, monkeypatch):
        monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", False)
        store = make_store(TypesSiteStore, {}, field_name="base_site_name")
        assert store.native_attr is not None


@pytest.mark.usefixtures("temporary_transaction", "install_module_test")
class TestNomenclaturesStore:
    @pytest.fixture(autouse=True)
    def clear_nomenclature_cache(self):
        get_nomenclature_type.cache_clear()
        yield
        get_nomenclature_type.cache_clear()

    def test_nomenclature_type_is_loaded(self):
        store = make_store(NomenclaturesStore, {"nomenclature_type": "TEST_METEO"})
        assert store["nomenclature_type"].mnemonique == "TEST_METEO"

    def test_default_storage_cols(self):
        store = make_store(NomenclaturesStore, {"nomenclature_type": "TEST_METEO"})
        assert store["storage_cols"] == ["id_nomenclature", "cd_nomenclature", "label_default"]

    def test_unknown_nomenclature_type_is_rejected(self):
        with pytest.raises(ValidationError):
            make_store(NomenclaturesStore, {"nomenclature_type": "UNKNOWN_TYPE_XYZ"})

    def test_wire_type_is_list_of_int(self):
        store = make_store(NomenclaturesStore, {"nomenclature_type": "TEST_METEO"})
        assert store.get_wire_type() == list[int]
