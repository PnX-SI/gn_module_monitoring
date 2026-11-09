import json

import pytest
import sqlalchemy as sa
from marshmallow import ValidationError

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.modules import get_module
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.tools.stores.relationships.m2m import (
    AreasStore,
    DatasetsStore,
    NomenclaturesStore,
    TypesSiteStore,
    UsersStore,
)
from gn_module_monitoring.tools.stores.relationships.utils import get_nomenclature_type
from gn_module_monitoring.tools.utils import schema_context


def make_store(store_cls, config, field_name="my_field"):
    with schema_context(
        entity=ENTITY_MAP["site"], field_name=field_name, module=get_module("test")
    ):
        return store_cls(config)


@pytest.fixture
def types_site_relationship():
    return sa.inspect(TMonitoringSites).relationships["types_site"]


@pytest.mark.usefixtures("temporary_transaction", "install_module_test_with_config")
class TestTypesSiteStore:
    def test_api_type_is_list_of_int(self):
        assert make_store(TypesSiteStore, {}, field_name="types_site").get_api_type() == list[int]

    def test_is_suitable_for_types_site_relationship(self, types_site_relationship):
        assert TypesSiteStore.is_suitable_for_relationship(types_site_relationship)

    def test_is_not_suitable_for_other_model(self, types_site_relationship):
        assert not AreasStore.is_suitable_for_relationship(types_site_relationship)

    def test_is_not_suitable_without_secondary(self):
        many_to_one = sa.inspect(TMonitoringSites).relationships["sites_group"]
        assert many_to_one.secondary is None
        assert not TypesSiteStore.is_suitable_for_relationship(many_to_one)

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


@pytest.mark.usefixtures("temporary_transaction", "install_module_test_with_config")
class TestNomenclaturesStore:
    @pytest.fixture(autouse=True)
    def clear_nomenclature_cache(self):
        get_nomenclature_type.cache_clear()
        yield
        get_nomenclature_type.cache_clear()

    def test_nomenclature_type_is_loaded(self):
        store = make_store(NomenclaturesStore, {"nomenclature_type": "TEST_METEO"})
        assert store.nomenclature_type.mnemonique == "TEST_METEO"

    def test_default_storage_cols(self):
        store = make_store(NomenclaturesStore, {"nomenclature_type": "TEST_METEO"})
        assert store["storage_cols"] == ["id_nomenclature", "cd_nomenclature", "label_default"]

    def test_unknown_nomenclature_type_is_rejected(self):
        with pytest.raises(ValidationError):
            make_store(NomenclaturesStore, {"nomenclature_type": "UNKNOWN_TYPE_XYZ"})

    def test_api_type_is_list_of_int(self):
        store = make_store(NomenclaturesStore, {"nomenclature_type": "TEST_METEO"})
        assert store.get_api_type() == list[int]


@pytest.mark.usefixtures("temporary_transaction")
class TestManyToManyStorage:
    def test_default_storage_is_list_of_pks(self, users):
        id_role = users["user"].id_role
        store = make_store(UsersStore, {})
        instances = store.get_field().deserialize([id_role])
        stored = store.to_storage(instances)
        assert stored == [id_role]
        assert json.dumps(stored)
        assert store.from_storage(stored) == [id_role]

    def test_storage_cols_are_list_of_objects(self, users):
        user = users["user"]
        store = make_store(UsersStore, {"storage_cols": ["id_role", "identifiant"]})
        instances = store.get_field().deserialize([user.id_role])
        stored = store.to_storage(instances)
        assert stored == [{"id_role": user.id_role, "identifiant": user.identifiant}]
        assert store.from_storage(stored) == [user.id_role]

    def test_storage_col_is_list_of_values(self, datasets):
        dataset = datasets["orphan_dataset"]
        store = make_store(DatasetsStore, {"storage_col": "dataset_name"})
        instances = store.get_field().deserialize([dataset.id_dataset])
        stored = store.to_storage(instances)
        assert stored == [dataset.dataset_name]
        assert store.from_storage(stored) == [dataset.id_dataset]

    def test_storage_col_unknown_value_is_rejected(self):
        store = make_store(DatasetsStore, {"storage_col": "dataset_name"})
        with pytest.raises(ValueError):
            store.from_storage(["jeu de données inexistant"])

    def test_none_is_kept(self):
        store = make_store(UsersStore, {})
        assert store.to_storage(None) is None
        assert store.from_storage(None) is None

    def test_empty_list_is_kept(self):
        store = make_store(UsersStore, {})
        assert store.to_storage([]) == []
        assert store.from_storage([]) == []


@pytest.mark.usefixtures("temporary_transaction")
class TestLoadInstances:
    def test_python_type_is_list_of_model(self):
        store = make_store(TypesSiteStore, {})
        assert store.get_python_type() == list[TypesSiteStore.get_model()]

    def test_field_loads_instances(self, users):
        id_role = users["user"].id_role
        store = make_store(UsersStore, {})
        (instance,) = store.get_field().deserialize([id_role])
        assert instance.id_role == id_role

    def test_field_rejects_unknown_id(self):
        store = make_store(UsersStore, {})
        with pytest.raises(ValidationError):
            store.get_field().deserialize([-1])

    def test_field_serializes_pks_unchanged(self, users):
        id_role = users["user"].id_role
        store = make_store(UsersStore, {})
        assert store.get_field()._serialize([id_role], None, None) == [id_role]
