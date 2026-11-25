"""
Types des colonnes de la table transitoire d'import (`get_imports_table_metadata`).

Le caractère natif d'un champ est lu sur son store (`store.native_attr`) dans l'entité chargée
du module `demo` : un champ natif a un store lié à une colonne du modèle, un champ additionnel
n'en a pas et est stocké dans la colonne `<entité>_data`.
"""

from sqlalchemy import Boolean, Date, Float, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB

from gn_module_monitoring.command.imports.sql import get_imports_table_metadata
from gn_module_monitoring.modules.entities import ENTITY_MAP

MODULE_CODE = "demo"


def _field(entity_code, entity_field_name, name_field=None):
    """Champ de protocole : le nom d'import vient de l'entité, le type de colonne de son store."""
    if name_field is None:
        name_field = ENTITY_MAP[entity_code].import_actions_class.get_field_name(entity_field_name)
    return {
        "name_field": name_field,
        "source_field": f"src_{name_field}",
        "dest_field": name_field,
    }


PROTOCOL_DATA = {
    "site": {
        "fields": [
            # natifs : store lié à une colonne de t_base_sites
            _field("site", "altitude_min"),
            _field("site", "first_use_date"),
            _field("site", "uuid_base_site", name_field="uuid_base_site"),
            # additionnels : store sans colonne de t_base_sites
            _field("site", "demo_number_float"),
            _field("site", "demo_date"),
            _field("site", "demo_uuid"),
            _field("site", "demo_nomenclature"),
            _field("site", "demo_bool"),
        ]
    },
    "visit": {"fields": [_field("visit", "visit_date_min")]},
    "observation": {
        "fields": [
            _field("observation", "comments"),
            _field("observation", "demo_count"),
        ]
    },
}


def _table():
    return get_imports_table_metadata(MODULE_CODE, PROTOCOL_DATA)


def test_native_integer_is_integer():
    assert isinstance(_table().c["s__altitude_min"].type, Integer)


def test_native_date_is_date():
    assert isinstance(_table().c["s__first_use_date"].type, Date)


def test_native_uuid_is_uuid():
    assert isinstance(_table().c["uuid_base_site"].type, Uuid)


def test_native_date_of_visit_is_date():
    assert isinstance(_table().c["v__visit_date_min"].type, Date)


def test_native_text_is_string():
    assert isinstance(_table().c["o__comments"].type, String)


def test_native_integer_of_observation_is_integer():
    assert isinstance(_table().c["o__demo_count"].type, Integer)


def test_additional_number_is_float():
    assert isinstance(_table().c["s__demo_number_float"].type, Float)


def test_additional_date_is_text():
    column_type = _table().c["s__demo_date"].type
    assert isinstance(column_type, String)
    assert not isinstance(column_type, Date)


def test_additional_uuid_is_text():
    column_type = _table().c["s__demo_uuid"].type
    assert isinstance(column_type, String)
    assert not isinstance(column_type, Uuid)


def test_additional_relation_is_integer():
    assert isinstance(_table().c["s__demo_nomenclature"].type, Integer)


def test_additional_boolean_is_boolean():
    assert isinstance(_table().c["s__demo_bool"].type, Boolean)


def test_source_column_is_kept_for_every_field():
    table = _table()
    assert isinstance(table.c["src_s__demo_date"].type, String)
    assert isinstance(table.c["src_s__altitude_min"].type, String)


def test_data_column_is_nullable_jsonb_per_entity():
    table = _table()
    for entity_code in PROTOCOL_DATA:
        column = table.c[f"{entity_code}_data"]
        assert isinstance(column.type, JSONB)
        assert column.nullable
