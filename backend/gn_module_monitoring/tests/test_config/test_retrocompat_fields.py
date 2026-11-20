"""
Rétro-compatibilité des définitions de champ (21/11).

- STRICT : aucune conversion. L'ancien format (`type_widget`, `type_util`, clés plates) est refusé.
- Non STRICT : `type_widget` / `type_util` définissent `widget.type` / `store.type`. Aucune clé n'est
  retirée du premier niveau : les clés non reconnues par les schémas sont ignorées (EXCLUDE).
"""

from copy import deepcopy

import pytest
from marshmallow import ValidationError

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.entities.fields import (
    EntityFieldConfigSchema,
    handle_retrocompat_field_definition,
)
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.utils import schema_context


@pytest.fixture
def strict(app, monkeypatch):
    monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", True)


@pytest.fixture
def non_strict(app, monkeypatch):
    monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", False)


def load_field(definition, field_name="field_test"):
    definition = {"name": field_name, **definition}
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        return EntityFieldConfigSchema().load(definition)


# (a) STRICT : l'ancien format est rejeté


def test_strict_rejects_legacy_type_widget(strict):
    with pytest.raises(ValidationError):
        load_field({"type_widget": "text", "attribut_label": "Nom"})


def test_strict_rejects_legacy_type_util(strict):
    with pytest.raises(ValidationError):
        load_field({"type_util": "dataset"})


# (c) STRICT : le format courant passe, sans appel de conversion


def test_strict_leaves_new_format_definition_untouched(strict):
    definition = {"widget": {"type": "text"}, "store": {"type": "string"}, "required": "js-expr"}
    snapshot = deepcopy(definition)
    result = handle_retrocompat_field_definition(definition)
    assert result == snapshot  # `required` non booléen n'est pas converti en STRICT
    with pytest.raises(ValidationError):
        load_field({"widget": {"type": "text"}, "store": {"type": "string"}, "required": "js-expr"})


def test_strict_accepts_new_format_definition(strict):
    field = load_field({"widget": {"type": "text"}, "store": {"type": "string"}, "required": True})
    assert field["required"] is True


# (b) non STRICT : conversion de type_widget / type_util, sans retrait de clé


def test_non_strict_converts_type_widget_to_widget_type(non_strict):
    converted = handle_retrocompat_field_definition({"type_widget": "textarea", "attribut_label": "X"})
    assert converted["widget"]["type"] == "textarea"
    assert converted["widget"]["attribut_label"] == "X"
    assert "type_widget" not in converted  # pop au premier niveau (conversion)


@pytest.mark.parametrize(
    "definition,expected_type",
    [
        ({"type_util": "dataset", "multi_select": True}, "datasets"),
        ({"type_util": "dataset"}, "dataset"),
        ({"type_util": "module", "multiple": True}, "modules"),
        ({"type_util": "user", "multiple": True}, "users"),
        ({"type_util": "user"}, "user"),
    ],
)
def test_non_strict_converts_type_util_to_store_type(non_strict, definition, expected_type):
    converted = handle_retrocompat_field_definition(definition)
    assert converted["store"]["type"] == expected_type


def test_non_strict_keeps_top_level_keys_untouched(non_strict):
    # Aucune clé n'est retirée du premier niveau (EXCLUDE les ignore au chargement)
    converted = handle_retrocompat_field_definition({"type_widget": "text", "zzz": 1})
    assert converted["zzz"] == 1


def test_non_strict_unknown_key_is_ignored_at_load(non_strict):
    field = load_field({"widget": {"type": "text"}, "store": {"type": "string"}, "zzz": 1})
    assert "zzz" not in field


def test_non_strict_legacy_definition_loads(non_strict):
    field = load_field({"type_widget": "text", "attribut_label": "Nom"})
    assert field["widget"]["type"] == "text"


def test_non_strict_required_js_becomes_widget_required_js(non_strict):
    # (d) required JavaScript -> widget.required_js, required devient False
    converted = handle_retrocompat_field_definition({"required": "({value}) => true"})
    assert converted["widget"]["required_js"] == "({value}) => true"
    assert converted["required"] is False


def test_non_strict_site_widget_must_be_hidden(non_strict):
    with pytest.raises(ValidationError):
        handle_retrocompat_field_definition({"type_widget": "site"})


def test_non_strict_no_self_reference_when_widget_is_given(non_strict):
    # Régression : `widget.update(data)` créait une référence cyclique
    converted = handle_retrocompat_field_definition({"type_widget": "text", "widget": {"type": "select"}})
    assert converted["widget"]["type"] == "text"
    assert "widget" not in converted["widget"]


def test_input_is_not_mutated(non_strict):
    definition = {"type_widget": "text", "required": "js"}
    snapshot = deepcopy(definition)
    handle_retrocompat_field_definition(definition)
    assert definition == snapshot


def test_default_value_absent_is_none(non_strict):
    field = load_field({"widget": {"type": "text"}, "store": {"type": "string"}})
    assert field.get("default_value") is None
