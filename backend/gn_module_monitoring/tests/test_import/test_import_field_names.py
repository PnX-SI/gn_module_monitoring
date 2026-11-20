from types import SimpleNamespace

import pytest

from gn_module_monitoring.command.imports.fields import prepare_fields
from gn_module_monitoring.config.entities.base import compile_entity_cel_expressions
from gn_module_monitoring.config.entities.fields import EntityFieldConfigSchema
from gn_module_monitoring.modules import get_module
from gn_module_monitoring.modules.entities import ENTITY_MAP
from gn_module_monitoring.monitoring.import_actions.field_names import (
    build_field_names,
)
from gn_module_monitoring.tools.stores.type import StringStore
from gn_module_monitoring.tools.utils import CELValidationsField, schema_context


def make_field(field_name, required_cel=None, validate_cel=None, hidden_cel=None):
    with schema_context(entity=ENTITY_MAP["site"], field_name=field_name):
        store = StringStore(
            {},
            required_cel=required_cel,
            validate_cel=CELValidationsField().deserialize(validate_cel) if validate_cel else None,
        )
    return {"store": store, "widget": {"hidden_cel": hidden_cel} if hidden_cel else {}}


def make_entity(fields, validate_cel=None, entity_code="site"):
    """Entité minimale (instance de la classe d'entité). `fields` = {nom: {"required_cel", ...}}."""
    data = {
        "fields": {name: make_field(name, **config) for name, config in fields.items()},
        "validate_cel": CELValidationsField().deserialize(validate_cel) if validate_cel else None,
    }
    compile_entity_cel_expressions(data)
    entity = object.__new__(ENTITY_MAP[entity_code])
    entity.data = data
    return entity


def load_field(entity_code, field_name, config):
    """Champ chargé comme la configuration sur disque (EntityFieldConfigSchema)."""
    with schema_context(entity=ENTITY_MAP[entity_code]):
        return EntityFieldConfigSchema().load({"name": field_name, **config})


@pytest.mark.parametrize(
    "entity_code, field_name, expected",
    [
        ("site", "roost_type", "s__roost_type"),
        ("visit", "meteo", "v__meteo"),
        ("observation", "stade", "o__stade"),
        ("observation_detail", "count", "d__count"),
        ("sites_group", "name", "g__name"),
        # identifiants : nom nu
        ("observation_detail", "id_observation_detail", "id_observation_detail"),
        # identifiant de l'entité : nom nu (la liste IGNORED_IMPORT_FIELDS n'intervient pas ici)
        ("site", "id_base_site", "id_base_site"),
        ("visit", "id_base_visit", "id_base_visit"),
        ("observation", "id_observation", "id_observation"),
        ("sites_group", "id_sites_group", "id_sites_group"),
        # autres identifiants : préfixés (les champs synthétiques portent un import_name explicite)
        ("visit", "uuid_base_visit", "v__uuid_base_visit"),
        ("visit", "id_base_site", "v__id_base_site"),
    ],
)
def test_get_import_column_name(entity_code, field_name, expected):
    assert ENTITY_MAP[entity_code].get_import_column_name(field_name) == expected


def test_build_field_names_excludes_ignored_fields():
    """IC1 : un champ de IGNORED_IMPORT_FIELDS n'a pas d'import field name."""
    entity = make_entity({"id_base_site": {}, "uuid_base_site": {}, "kind": {}})
    names = build_field_names("site", entity)
    assert names.import_to_entity == {"s__kind": "kind"}
    assert set(names.ignored_entity_fields) == {"id_base_site", "uuid_base_site"}


def test_build_field_names_maps_fields_and_ignores_generated_ones():
    entity = make_entity(
        {
            "kind": {},
            "value": {},
            "id_base_site": {},
            "id_sites_group": {},
        }
    )
    names = build_field_names("site", entity)
    assert names.import_to_entity == {"s__kind": "kind", "s__value": "value"}
    assert names.ignored_entity_fields == {
        "id_base_site": "champ ignoré à l'import (IGNORED_IMPORT_FIELDS)",
        "id_sites_group": "champ ignoré à l'import (IGNORED_IMPORT_FIELDS)",
    }
    assert names.ignored_cel_variables == {}
    assert names.import_field_name_of("value") == "s__value"
    assert names.import_field_name_of("id_base_site") is None


def test_cel_variable_on_ignored_field_is_reported():
    entity = make_entity(
        {
            "kind": {"required_cel": 'fields.id_sites_group != null'},
            "id_sites_group": {},
        }
    )
    names = build_field_names("site", entity)
    assert names.ignored_cel_variables == {
        "fields.id_sites_group": "champ ignoré à l'import (IGNORED_IMPORT_FIELDS)",
    }


def test_entity_cel_variable_is_checked():
    entity = make_entity(
        {"kind": {}, "value": {"validate_cel": ["fields.value > 0"]}},
        validate_cel=["fields.kind != fields.value"],
        entity_code="visit",
    )
    names = build_field_names("visit", entity)
    assert names.ignored_cel_variables == {}
    assert names.import_to_entity == {"v__kind": "kind", "v__value": "value"}


def test_field_names_agree_with_prepare_fields():
    """La règle de correspondance doit donner les mêmes import field names que l'import réel."""
    entity = object.__new__(ENTITY_MAP["observation"])
    entity.data = {
        "label": "Observation",
        "fields": {
            "stade": load_field("observation", "stade", {"widget": {"type": "text"}}),
            "count": load_field("observation", "count", {"widget": {"type": "number"}}),
            "id_observation": load_field(
                "observation", "id_observation", {"store": {"type": "integer"}}
            ),
            "id_base_visit": load_field("observation", "id_base_visit", {"store": {"type": "integer"}}),
            "medias": load_field(
                "observation", "medias", {"store": {"type": "dummy"}, "widget": {"type": "text"}}
            ),
        },
    }
    prepared = prepare_fields(entity, id_destination=1, parent_data=None)
    imported = {f["name_field"] for f in prepared["fields"]}

    names = build_field_names("observation", entity)
    assert set(names.import_to_entity) == imported
    assert names.import_to_entity == {"o__stade": "stade", "o__count": "count"}


@pytest.mark.parametrize("module_code", ["demo", "test_indi"])
def test_module_entities_field_names(module_code):
    """Vérification sur les modules de référence : toutes les variables CEL doivent être mappées."""
    module = get_module(module_code)
    for entity_code, entity in module.entities.items():
        names = build_field_names(entity_code, entity)
        # un import field name ne désigne qu'un seul entity field name
        assert len(names.import_to_entity) == len(set(names.import_to_entity.values()))
        # toute variable CEL de l'entité doit désigner un champ mappé (D-IC9)
        assert names.ignored_cel_variables == {}, (entity_code, names.ignored_cel_variables)
