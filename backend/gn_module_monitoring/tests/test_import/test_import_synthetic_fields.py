"""
Champs synthétiques de l'import (`get_synthetic_field_specs`) chargés en mode strict.

Un store integer exige un widget qui renvoie `int` : le widget `number` ne le renvoie que si
`step` est entier (`NumberWidget.get_api_type`). Sans `step`, il renvoie `float` et le mode strict
rejette l'incohérence (config/entities/fields.py).
"""

import pytest
from marshmallow import ValidationError

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.command.imports.protocol import get_synthetic_field_specs
from gn_module_monitoring.config.entities.fields import EntityFieldConfigSchema
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.tools.utils import schema_context


def make_entity(entity_code, data):
    entity = object.__new__(ENTITY_MAP[entity_code])
    entity.data = data
    return entity


def synthetic_specs(entity_code):
    data = {"geom_field_name": "geom"} if entity_code == "site" else {}
    entity = make_entity(entity_code, data)
    return entity, get_synthetic_field_specs(entity_code, entity, 2154)


@pytest.mark.parametrize("entity_code", ["site", "visit", "observation"])
def test_integer_synthetic_fields_have_integer_widget(entity_code):
    _, specs = synthetic_specs(entity_code)
    integer_specs = [s for s in specs if s["config"]["store"]["type"] == "integer"]
    assert integer_specs, "au moins un identifiant entier attendu"
    for spec in integer_specs:
        assert spec["config"]["widget"]["step"] == 1, spec["key"]


# Identifiants hérités (héritage joint) : leur attribut natif porte 2 colonnes pour le site et
# l'observation, et le store integer refuse une colonne multiple (tools/stores/type.py,
# « doit être utilisé avec une colonne simple »). Décision à prendre : voir PROGRESS.md (20/11).
INHERITED_ID_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="store integer sur identifiant hérité (plusieurs colonnes) refusé en strict",
)


@pytest.mark.parametrize(
    "entity_code",
    [
        pytest.param("site", marks=INHERITED_ID_XFAIL),
        pytest.param("visit", marks=INHERITED_ID_XFAIL),
        pytest.param("observation", marks=INHERITED_ID_XFAIL),
    ],
)
def test_synthetic_fields_load_in_strict_mode(app, monkeypatch, entity_code):
    monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", True)
    entity, specs = synthetic_specs(entity_code)
    for spec in specs:
        with schema_context(entity=entity):
            EntityFieldConfigSchema().load({"name": spec["key"], **spec["config"]})


# Nom sans attribut natif : seule la cohérence widget/store est testée.
TEST_FIELD_NAME = "id_test_entier"


def test_number_widget_without_step_is_rejected_with_integer_store(app, monkeypatch):
    monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", True)
    entity = make_entity("site", {})
    config = {
        "store": {"type": "integer"},
        "widget": {"type": "number", "hidden": True},
    }
    with schema_context(entity=entity):
        with pytest.raises(ValidationError, match="Incohérence de type"):
            EntityFieldConfigSchema().load({"name": TEST_FIELD_NAME, **config})


def test_number_widget_with_integer_step_is_accepted_with_integer_store(app, monkeypatch):
    monkeypatch.setitem(app.config[MODULE_CODE], "STRICT", True)
    entity = make_entity("site", {})
    config = {
        "store": {"type": "integer"},
        "widget": {"type": "number", "step": 1, "hidden": True},
    }
    with schema_context(entity=entity):
        EntityFieldConfigSchema().load({"name": TEST_FIELD_NAME, **config})
