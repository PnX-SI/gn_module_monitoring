"""
Fonctions pures du diff entre le protocole voulu et l'existant (`process_import`, `check`) :
types PostgreSQL, colonnes de la table transitoire, attributs de bib_fields,
bib_entities. Pas de base de données.
"""

from gn_module_monitoring.command.imports.fields import get_field_changes, has_field_changes
from gn_module_monitoring.command.imports.protocol import (
    compare_bib_entities,
    compare_protocol_fields,
    format_protocol_diff,
)
from gn_module_monitoring.command.imports.sql import (
    compare_transient_columns,
    normalize_pg_type,
)


def test_equivalent_pg_types_are_not_differences():
    assert normalize_pg_type("FLOAT") == normalize_pg_type("DOUBLE PRECISION")
    assert normalize_pg_type("TIMESTAMP WITHOUT TIME ZONE") == normalize_pg_type("TIMESTAMP")
    assert normalize_pg_type("CHARACTER VARYING(255)") == normalize_pg_type("VARCHAR(255)")
    assert normalize_pg_type("VARCHAR[]") == normalize_pg_type("varchar[]")

    diff = compare_transient_columns(
        {"s__float": "DOUBLE PRECISION", "d": "TIMESTAMP WITHOUT TIME ZONE"},
        {"s__float": "FLOAT", "d": "TIMESTAMP"},
    )
    assert diff == {"added": [], "removed": [], "type_changed": []}


def test_uuid_char32_versus_uuid_is_detected():
    assert normalize_pg_type("CHAR(32)") != normalize_pg_type("UUID")

    diff = compare_transient_columns(
        {"uuid_base_site": "UUID"},
        {"uuid_base_site": "CHAR(32)"},
    )
    assert diff["type_changed"] == [
        {"name": "uuid_base_site", "db": "UUID", "expected": "CHAR(32)"}
    ]
    assert diff["added"] == [] and diff["removed"] == []


def test_column_added_or_removed_is_detected():
    diff = compare_transient_columns(
        {"id_import": "INTEGER", "old_col": "VARCHAR"},
        {"id_import": "INTEGER", "new_col": "VARCHAR"},
    )
    assert diff["added"] == ["new_col"]
    assert diff["removed"] == ["old_col"]
    assert diff["type_changed"] == []


def test_type_field_params_change_is_detected_as_full_json_equality():
    existing = {
        "fr_label": "Libellé",
        "type_field": "select",
        "type_field_params": {"values": [1, 2], "multiple": False},
    }
    new = {
        "fr_label": "Libellé",
        "type_field": "select",
        "type_field_params": {"values": [1, 2, 3], "multiple": False},
    }
    changes = get_field_changes(existing, new)
    assert changes == [
        {
            "attr": "type_field_params",
            "db": {"values": [1, 2], "multiple": False},
            "expected": {"values": [1, 2, 3], "multiple": False},
        }
    ]
    assert has_field_changes(existing, new)


def test_type_field_params_same_content_different_key_order_is_not_a_change():
    existing = {"type_field_params": {"a": 1, "b": [1, 2]}}
    new = {"type_field_params": {"b": [1, 2], "a": 1}}
    assert get_field_changes(existing, new) == []


def test_deleted_bib_field_is_detected():
    existing = [
        {"name_field": "s__keep", "id_field": 1, "dest_field": "keep"},
        {"name_field": "s__removed", "id_field": 2, "dest_field": "removed"},
    ]
    new = [{"name_field": "s__keep", "dest_field": "keep"}]
    to_add, to_update, to_delete = compare_protocol_fields(existing, new)
    assert to_add == [] and to_update == []
    assert [field["name_field"] for field in to_delete] == ["s__removed"]
    assert to_delete[0]["id_field"] == 2


def test_bib_entities_label_order_parent_and_uuid_are_compared():
    base = {
        "label": "Site",
        "order": 1,
        "validity_column": "site_valid",
        "destination_table_schema": "gn_monitoring",
        "destination_table_name": "t_base_sites",
        "parent": None,
        "unique_field": "id_base_site",
        "uuid_field": "uuid_base_site",
    }
    expected = [{**base, "code": "site"}]
    existing = [
        {
            **base,
            "code": "site",
            "label": "Ancien",
            "order": 2,
            "parent": "sites_group",
            "uuid_field": "uuid_site_old",
        }
    ]
    diff = compare_bib_entities(existing, expected)
    assert diff["added"] == [] and diff["removed"] == []
    assert {(c["attr"], c["db"], c["expected"]) for c in diff["changed"]} == {
        ("label", "Ancien", "Site"),
        ("order", 2, 1),
        ("parent", "sites_group", None),
        ("uuid_field", "uuid_site_old", "uuid_base_site"),
    }


def test_bib_entities_added_and_removed_are_compared_by_code():
    base = {
        "label": "X",
        "order": 1,
        "validity_column": "x_valid",
        "destination_table_schema": "gn_monitoring",
        "destination_table_name": None,
        "parent": None,
        "unique_field": "id_x",
        "uuid_field": "uuid_x",
    }
    diff = compare_bib_entities(
        [{**base, "code": "old"}],
        [{**base, "code": "new"}],
    )
    assert diff["added"] == ["new"]
    assert diff["removed"] == ["old"]


def test_format_protocol_diff_lists_every_difference():
    diff = {
        "label": None,
        "fields": {
            "added": [{"name_field": "s__new"}],
            "updated": [
                {
                    "name_field": "s__mod",
                    "changes": [{"attr": "fr_label", "db": "A", "expected": "B"}],
                    "new": {},
                }
            ],
            "deleted": [{"name_field": "s__del"}],
        },
        "entities": {"added": [], "removed": [], "changed": []},
        "transient_table": {
            "table": "gn_imports.t_imports_demo",
            "exists": True,
            "added": ["c1"],
            "removed": ["c2"],
            "type_changed": [{"name": "uuid_base_site", "db": "UUID", "expected": "CHAR(32)"}],
        },
    }
    lines = format_protocol_diff(diff)
    text = "\n".join(lines)
    assert "s__new" in text and "s__mod" in text and "s__del" in text
    assert "fr_label" in text
    assert "colonnes à ajouter : c1" in text
    assert "colonnes à supprimer : c2" in text
    assert "uuid_base_site : UUID -> CHAR(32)" in text
