import datetime
import json
import uuid
from types import SimpleNamespace

import pytest
from marshmallow import ValidationError

from gn_module_monitoring.config.entities.base import compile_entity_cel_expressions
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.modules.entities.base import BaseEntity
from gn_module_monitoring.tools.stores.type import (
    DateStore,
    DateTimeStore,
    IntegerStore,
    StringStore,
    UUIDStore,
)
from gn_module_monitoring.tools.stores.relationships.m2m import (
    AreasStore,
    DatasetsStore,
    UsersStore,
)
from gn_module_monitoring.tools.stores.relationships.m2o import SiteStore, UserStore
from gn_module_monitoring.tools.utils import schema_context


def make_store(store_cls, field_name="value", data=None):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        return store_cls(data or {})


def build_schema(stores):
    site_cls = ENTITY_MAP["site"]
    entity_data = {"fields": {name: {"store": store} for name, store in stores.items()}}
    compile_entity_cel_expressions(entity_data)
    fake = SimpleNamespace(
        data=entity_data,
        model_schema_class=site_cls.model_schema_class,
    )
    fake._build_extra_data_schema = lambda extra: BaseEntity._build_extra_data_schema(fake, extra)
    return BaseEntity._build_extended_schema(fake, ())


class TestToStorage:
    def test_date_is_iso_string(self):
        store = make_store(DateStore)
        assert store.to_json_storage(datetime.date(2024, 1, 2)) == "2024-01-02"

    def test_date_refuses_datetime(self):
        # Contrat explicite : la colonne est une date, un datetime n'est pas accepté
        with pytest.raises(TypeError):
            make_store(DateStore).to_json_storage(datetime.datetime(2024, 1, 2, 8, 30))

    def test_datetime_refuses_date(self):
        with pytest.raises(TypeError):
            make_store(DateTimeStore).to_json_storage(datetime.date(2024, 1, 2))

    def test_date_round_trip(self):
        store = make_store(DateStore)
        assert store.from_json_storage(store.to_json_storage(datetime.date(2024, 1, 2))) == datetime.date(2024, 1, 2)

    def test_datetime_round_trip(self):
        store = make_store(DateTimeStore)
        value = datetime.datetime(2024, 1, 2, 8, 30)
        assert store.from_json_storage(store.to_json_storage(value)) == value

    def test_datetime_is_iso_string(self):
        store = make_store(DateTimeStore)
        value = datetime.datetime(2024, 1, 2, 8, 30)
        assert store.to_json_storage(value) == "2024-01-02T08:30:00"

    def test_uuid_is_string(self):
        store = make_store(UUIDStore)
        value = uuid.UUID(int=1)
        assert store.to_json_storage(value) == str(value)

    @pytest.mark.parametrize("store_cls", [DateStore, DateTimeStore, UUIDStore])
    def test_none_is_kept(self, store_cls):
        assert make_store(store_cls).to_json_storage(None) is None

    def test_plain_value_is_kept(self):
        assert make_store(IntegerStore).to_json_storage(3) == 3
        assert make_store(StringStore).to_json_storage("abc") == "abc"


class TestFromStorage:
    def test_date_from_iso_string(self):
        store = make_store(DateStore)
        assert store.from_json_storage("2024-01-02") == datetime.date(2024, 1, 2)

    def test_datetime_from_iso_string(self):
        store = make_store(DateTimeStore)
        assert store.from_json_storage("2024-01-02T08:30:00") == datetime.datetime(2024, 1, 2, 8, 30)

    def test_uuid_from_string(self):
        store = make_store(UUIDStore)
        assert store.from_json_storage(str(uuid.UUID(int=1))) == uuid.UUID(int=1)

    @pytest.mark.parametrize("store_cls", [DateStore, DateTimeStore, UUIDStore])
    def test_roundtrip(self, store_cls):
        store = make_store(store_cls)
        value = {
            DateStore: datetime.date(2024, 1, 2),
            DateTimeStore: datetime.datetime(2024, 1, 2, 8, 30),
            UUIDStore: uuid.UUID(int=1),
        }[store_cls]
        assert store.from_json_storage(store.to_json_storage(value)) == value


class TestApiType:
    def test_field_serializes_python_value_to_api_format(self):
        field = make_store(DateStore).get_field()
        assert field._serialize(datetime.date(2024, 1, 2), None, None) == "2024-01-02"

    def test_api_type_is_renamed(self):
        assert make_store(IntegerStore).get_api_type() is int


class TestExtendedSchemaStorage:
    def test_loaded_extra_values_are_json_safe(self):
        schema = build_schema({"day": make_store(DateStore, "day")})
        loaded = schema(only=["+data", "+medias"]).load({"day": "2024-01-02"})
        assert loaded.data == {"day": "2024-01-02"}
        assert json.dumps(loaded.data)

    def test_dump_reads_stored_values_back_to_api_format(self):
        schema = build_schema({"day": make_store(DateStore, "day")})
        obj = SimpleNamespace(data={"day": "2024-01-02"})
        assert schema(only=["+data", "+medias"]).dump(obj)["day"] == "2024-01-02"

    def test_dump_ignores_keys_missing_from_configuration(self):
        schema = build_schema({"day": make_store(DateStore, "day")})
        obj = SimpleNamespace(data={"day": "2024-01-02", "removed": "x"})
        dumped = schema(only=["+data", "+medias"]).dump(obj)
        assert dumped["day"] == "2024-01-02"
        assert "removed" not in dumped

    def test_invalid_api_value_is_rejected(self):
        schema = build_schema({"day": make_store(DateStore, "day")})
        with pytest.raises(ValidationError):
            schema(only=["+data", "+medias"]).load({"day": "pas une date"})

    def test_many_to_many_extra_values_are_stored_as_pks(self, datasets):
        ids = [datasets["orphan_dataset"].id_dataset]
        store = make_store(DatasetsStore, "my_datasets", {"storage_col": "dataset_name"})
        schema = build_schema({"my_datasets": store})
        loaded = schema(only=["+data", "+medias"]).load({"my_datasets": ids})
        assert loaded.data == {"my_datasets": [datasets["orphan_dataset"].dataset_name]}
        assert json.dumps(loaded.data)

    def test_many_to_many_extra_values_are_read_back_as_pks(self, datasets):
        ids = [datasets["orphan_dataset"].id_dataset]
        store = make_store(DatasetsStore, "my_datasets", {"storage_col": "dataset_name"})
        schema = build_schema({"my_datasets": store})
        loaded = schema(only=["+data", "+medias"]).load({"my_datasets": ids})
        obj = SimpleNamespace(data=loaded.data)
        assert schema(only=["+data", "+medias"]).dump(obj)["my_datasets"] == ids

    def test_many_to_many_unknown_id_is_rejected(self):
        schema = build_schema({"my_datasets": make_store(DatasetsStore, "my_datasets")})
        with pytest.raises(ValidationError):
            schema(only=["+data", "+medias"]).load({"my_datasets": [-1]})

    def test_many_to_many_update_replaces_stored_value(self, datasets):
        ids = [datasets["orphan_dataset"].id_dataset]
        store = make_store(DatasetsStore, "my_datasets", {"storage_col": "dataset_name"})
        schema = build_schema({"my_datasets": store})
        assert schema(only=["+data", "+medias"]).load({"my_datasets": ids}).data == {
            "my_datasets": [datasets["orphan_dataset"].dataset_name]
        }
        assert schema(only=["+data", "+medias"]).load({"my_datasets": []}).data == {
            "my_datasets": []
        }


@pytest.mark.usefixtures("temporary_transaction", "install_module_test_with_config")
class TestAreasExtendedSchemaStorage:
    def test_areas_of_type_are_stored_as_pks(self, dep_area):
        store = make_store(AreasStore, "my_areas", {"area_type_code": "DEP"})
        schema = build_schema({"my_areas": store})
        loaded = schema(only=["+data", "+medias"]).load({"my_areas": [dep_area.id_area]})
        assert loaded.data == {"my_areas": [dep_area.id_area]}
        assert json.dumps(loaded.data)
        assert schema(only=["+data", "+medias"]).dump(SimpleNamespace(data=loaded.data))[
            "my_areas"
        ] == [dep_area.id_area]

    def test_area_of_other_type_is_rejected(self, dep_area, other_type_area):
        store = make_store(AreasStore, "my_areas", {"area_type_code": "DEP"})
        schema = build_schema({"my_areas": store})
        with pytest.raises(ValidationError):
            schema(only=["+data", "+medias"]).load(
                {"my_areas": [dep_area.id_area, other_type_area.id_area]}
            )

    def test_unknown_area_is_rejected(self):
        store = make_store(AreasStore, "my_areas", {"area_type_code": "DEP"})
        schema = build_schema({"my_areas": store})
        with pytest.raises(ValidationError):
            schema(only=["+data", "+medias"]).load({"my_areas": [-1]})


class TestPythonType:
    @pytest.mark.parametrize(
        "store_cls, sample, expected",
        [
            (StringStore, "abc", str),
            (IntegerStore, 3, int),
            (DateStore, "2024-01-02", datetime.date),
            (DateTimeStore, "2024-01-02T08:30:00", datetime.datetime),
            (UUIDStore, str(uuid.UUID(int=1)), uuid.UUID),
        ],
    )
    def test_python_type_is_type_of_loaded_value(self, store_cls, sample, expected):
        store = make_store(store_cls)
        assert store.get_python_type() is expected
        assert isinstance(store.get_field().deserialize(sample), expected)

    def test_relationship_python_type_is_model(self):
        store = make_store(SiteStore)
        assert store.get_python_type() is SiteStore.get_model()

    def test_multiple_relationship_python_type_is_list_of_model(self):
        store = make_store(UsersStore)
        assert store.get_python_type() == list[UsersStore.get_model()]


class TestCheckStoredValue:
    def _errors(self, store, value):
        generator = store.check_stored_value(None, 7, "field", value, False)
        messages = []
        try:
            while True:
                messages.append(next(generator))
        except StopIteration as stop:
            return messages, stop.value

    @pytest.mark.parametrize("value", ["2024-01-02", None])
    def test_valid_date_has_no_error(self, value):
        messages, returned = self._errors(make_store(DateStore), value)
        assert messages == []
        assert returned == value

    @pytest.mark.parametrize("value", ["02/01/2024", "2024-1-2", "20240102", "2024-02-30", 20240102])
    def test_invalid_date_is_reported(self, value):
        messages, returned = self._errors(make_store(DateStore), value)
        assert len(messages) == 1
        assert "n'est pas une date ISO" in messages[0]
        assert returned == value

    @pytest.mark.parametrize("value", ["2024-01-02T08:30:00", "2024-01-02T08:30:00+02:00", None])
    def test_valid_datetime_has_no_error(self, value):
        messages, _ = self._errors(make_store(DateTimeStore), value)
        assert messages == []

    @pytest.mark.parametrize("value", ["2024-01-02", "02/01/2024 08:30", "2024-01-02 08:30:00"])
    def test_invalid_datetime_is_reported(self, value):
        messages, _ = self._errors(make_store(DateTimeStore), value)
        assert len(messages) == 1
        assert "datetime ISO 8601" in messages[0]
