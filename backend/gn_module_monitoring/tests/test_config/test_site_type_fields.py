"""
Champs spécifiques des types de site (P1, P2) : fusion statique dans la configuration du site.

Règle : un champ défini par un type de site a priorité sur le protocole ; le protocole, comme un
type, ne peut redéfinir un champ déjà défini (type ou natif) que par son widget.
"""

from types import SimpleNamespace

import pytest
from marshmallow import ValidationError

from gn_module_monitoring.config.entities.fields import handle_retrocompat_field_definition
from gn_module_monitoring.config.entities.site import SiteEntityConfigSchema
from gn_module_monitoring.monitoring.models import TMonitoringSites
from gn_module_monitoring.tools.utils import schema_context

SPEC_ROOST = {"type_widget": "text", "attribut_label": "Type de gite", "required": True}
SPEC_PLACE = {"type_widget": "text", "attribut_label": "Lieux-dit"}


def make_type(id_type, label, specific):
    return SimpleNamespace(
        id_nomenclature_type_site=id_type,
        config={"specific": specific},
        nomenclature=SimpleNamespace(label_default=label),
    )


def pre_load_with_types(types, data):
    """Appelle le pre_load du schéma du site avec les types donnés (sans base de données)."""
    module = SimpleNamespace(
        module=SimpleNamespace(types_site=types),
        substitutions={},
        entities_list=[],
    )
    entity = SimpleNamespace(module=module, model=TMonitoringSites)
    with schema_context(entity=entity):
        return SiteEntityConfigSchema().pre_load(data)


def assert_spec_in(field, spec):
    # Le pre_load de base ajoute des clés (name, ...) : chaque clé de la spec (au format courant,
    # après conversion de la rétro-compatibilité) doit être présente
    spec = handle_retrocompat_field_definition(spec)
    assert all(field[key] == value for key, value in spec.items())


# (a) Champ de type de site : présent dans fields, avec sa propre définition


def test_type_specific_field_is_merged_into_site_fields():
    data = pre_load_with_types([make_type(1, "Grotte", {"roost_type": SPEC_ROOST})], {})
    assert_spec_in(data["fields"]["roost_type"], SPEC_ROOST)


def test_type_field_has_priority_over_protocol_field_of_same_name():
    # Le protocole ne peut pas redéfinir le store d'un champ de type : erreur (clé interdite)
    types = [make_type(1, "Grotte", {"place_name": SPEC_PLACE})]
    data = {"fields": {"place_name": {"store": {"type": "string"}}}}
    with pytest.raises(ValidationError, match="place_name"):
        pre_load_with_types(types, data)


# (c) Le protocole ne redéfinit que le widget : passe, sur un champ de type ou natif


def test_protocol_can_redefine_widget_of_native_field():
    widget = {"type": "textarea", "attribut_label": "Description longue"}
    data = pre_load_with_types([], {"fields": {"base_site_description": {"widget": widget}}})
    assert_spec_in(data["fields"]["base_site_description"], {"widget": widget})


def test_protocol_widget_is_applied_over_type_field():
    types = [make_type(1, "Grotte", {"roost_type": SPEC_ROOST})]
    widget = {"type": "select", "attribut_label": "Gîte"}
    data = pre_load_with_types(types, {"fields": {"roost_type": {"widget": widget}}})
    assert data["fields"]["roost_type"]["widget"]["type"] == "select"
    assert data["fields"]["roost_type"]["widget"]["attribut_label"] == "Gîte"
    # Le format de type legacy est converti avant fusion : `type_widget` est devenu widget.type
    assert "type_widget" not in data["fields"]["roost_type"]
    assert data["fields"]["roost_type"]["widget"]["attribut_label"] == "Gîte"


# (b) Le protocole ne redéfinit pas autre chose que le widget


@pytest.mark.parametrize(
    "field_name,spec",
    [
        ("base_site_name", {"store": {"type": "string"}}),
        ("base_site_name", {"required": False}),
        ("roost_type", {"required_cel": "fields.x"}),
    ],
)
def test_protocol_cannot_redefine_store_or_required_of_existing_field(field_name, spec):
    types = [make_type(1, "Grotte", {"roost_type": SPEC_ROOST})]
    with pytest.raises(ValidationError, match=field_name):
        pre_load_with_types(types, {"fields": {field_name: spec}})


def test_protocol_new_field_can_have_full_spec():
    # Un champ qui n'existe ni dans un type ni en natif reste libre
    spec = {"store": {"type": "string"}, "required": True}
    data = pre_load_with_types([], {"fields": {"my_new_field": spec}})
    assert_spec_in(data["fields"]["my_new_field"], spec)


# (d) Un type de site ne redéfinit un champ natif que par son widget


def test_type_cannot_redefine_store_of_native_field():
    types = [make_type(1, "Grotte", {"base_site_name": {"store": {"type": "string"}}})]
    with pytest.raises(ValidationError, match="base_site_name"):
        pre_load_with_types(types, {})


def test_type_can_redefine_widget_of_native_field():
    widget = {"type": "textarea"}
    types = [make_type(1, "Grotte", {"base_site_description": {"widget": widget}})]
    data = pre_load_with_types(types, {})
    assert_spec_in(data["fields"]["base_site_description"], {"widget": widget})


# (e) P2 inchangé : conflits entre types, et identité d'un champ partagé


def test_shared_identical_field_is_merged_once():
    types = [
        make_type(1, "Grotte", {"roost_type": SPEC_ROOST}),
        make_type(2, "Mine", {"roost_type": dict(SPEC_ROOST)}),
    ]
    data = pre_load_with_types(types, {})
    assert_spec_in(data["fields"]["roost_type"], SPEC_ROOST)


def test_same_field_with_different_specs_in_two_types_raises():
    types = [
        make_type(1, "Grotte", {"roost_type": SPEC_ROOST}),
        make_type(2, "Mine", {"roost_type": {"type_widget": "number"}}),
    ]
    with pytest.raises(ValidationError, match="roost_type"):
        pre_load_with_types(types, {})


def test_legacy_protocol_flat_widget_is_accepted_on_type_field():
    # Ancienne clé `specific` du protocole, widget au format plat : converti avant fusion,
    # c'est un widget seul, donc accepté sur un champ de type
    types = [make_type(1, "Grotte", {"place_name": SPEC_PLACE})]
    data = pre_load_with_types(types, {"specific": {"place_name": {"type_widget": "textarea"}}})
    assert data["fields"]["place_name"]["widget"]["type"] == "textarea"
    assert "type_widget" not in data["fields"]["place_name"]


# Règle `required` (21/11) : false -> true autorisé ; true -> false seulement avec default_value


def test_required_false_to_true_is_allowed_on_native_field():
    # (a) base_site_description n'est pas requis dans le natif
    data = pre_load_with_types([], {"fields": {"base_site_description": {"required": True}}})
    assert data["fields"]["base_site_description"]["required"] is True


def test_required_true_to_false_without_default_value_is_rejected_on_native_field():
    # (b) base_site_name est requis dans le natif
    with pytest.raises(ValidationError, match="base_site_name"):
        pre_load_with_types([], {"fields": {"base_site_name": {"required": False}}})


def test_required_true_to_false_with_default_value_is_accepted():
    # (c) passage à false accepté avec une valeur par défaut
    spec = {"required": False, "default_value": "Inconnu"}
    data = pre_load_with_types([], {"fields": {"base_site_name": spec}})
    assert data["fields"]["base_site_name"]["required"] is False
    assert data["fields"]["base_site_name"]["default_value"] == "Inconnu"


def test_default_value_is_none_when_absent():
    # (d) pas de default_value dans la config : None
    data = pre_load_with_types([], {"fields": {"base_site_name": {"widget": {"type": "text"}}}})
    assert data["fields"]["base_site_name"].get("default_value") is None


def test_required_identical_is_tolerated():
    data = pre_load_with_types([], {"fields": {"base_site_name": {"required": True}}})
    assert data["fields"]["base_site_name"]["required"] is True


def test_required_true_to_false_without_default_value_is_accepted_on_type_field():
    # Champ de type : pas de colonne NOT NULL, donc relâcher `required` est autorisé sans default_value
    types = [make_type(1, "Grotte", {"roost_type": SPEC_ROOST})]  # SPEC_ROOST : required True
    data = pre_load_with_types(types, {"fields": {"roost_type": {"required": False}}})
    assert data["fields"]["roost_type"]["required"] is False


def test_required_true_to_false_with_default_value_is_accepted_on_type_field():
    types = [make_type(1, "Grotte", {"roost_type": SPEC_ROOST})]
    spec = {"required": False, "default_value": "barrage"}
    data = pre_load_with_types(types, {"fields": {"roost_type": spec}})
    assert data["fields"]["roost_type"]["required"] is False
    assert data["fields"]["roost_type"]["default_value"] == "barrage"


def test_type_redefinition_of_native_required_follows_same_rule():
    # (e) un type redéfinit required d'un natif : même règle
    with pytest.raises(ValidationError, match="base_site_name"):
        pre_load_with_types(
            [make_type(1, "Grotte", {"base_site_name": {"required": False}})], {}
        )
    data = pre_load_with_types(
        [make_type(1, "Grotte", {"base_site_name": {"required": False, "default_value": "x"}})], {}
    )
    assert data["fields"]["base_site_name"]["default_value"] == "x"


def test_protocol_required_is_checked_against_type_required_not_native():
    # Type : base_site_description non requis (natif) -> le type ne change pas required ;
    # le protocole le passe à true : autorisé
    types = [make_type(1, "Grotte", {"base_site_description": {"widget": {"type": "textarea"}}})]
    data = pre_load_with_types(types, {"fields": {"base_site_description": {"required": True}}})
    assert data["fields"]["base_site_description"]["required"] is True
    assert data["fields"]["base_site_description"]["widget"]["type"] == "textarea"


# default_value redéfinissable par le protocole ou par un type (21/11)


def test_protocol_can_redefine_default_value_of_native_field():
    # (a) natif
    data = pre_load_with_types([], {"fields": {"base_site_description": {"default_value": "N/A"}}})
    assert data["fields"]["base_site_description"]["default_value"] == "N/A"


def test_protocol_can_redefine_default_value_of_type_field():
    # (b) champ de type
    types = [make_type(1, "Grotte", {"place_name": SPEC_PLACE})]
    data = pre_load_with_types(types, {"fields": {"place_name": {"default_value": "Inconnu"}}})
    assert data["fields"]["place_name"]["default_value"] == "Inconnu"


@pytest.mark.parametrize("key,value", [("store", {"type": "string"}), ("required_cel", "fields.x")])
def test_other_keys_remain_forbidden_on_native_and_type_fields(key, value):
    # (c) autre clé interdite, sur natif comme sur type
    types = [make_type(1, "Grotte", {"place_name": SPEC_PLACE})]
    with pytest.raises(ValidationError, match="base_site_description"):
        pre_load_with_types([], {"fields": {"base_site_description": {key: value}}})
    with pytest.raises(ValidationError, match="place_name"):
        pre_load_with_types(types, {"fields": {"place_name": {key: value}}})


def test_required_true_to_false_uses_default_value_of_type_layer():
    # Choix documenté : sans default_value dans le bloc protocole, celle du type s'applique
    types = [make_type(1, "Grotte", {"roost_type": {**SPEC_ROOST, "default_value": "barrage"}})]
    data = pre_load_with_types(types, {"fields": {"roost_type": {"required": False}}})
    assert data["fields"]["roost_type"]["required"] is False
    assert data["fields"]["roost_type"]["default_value"] == "barrage"


def test_required_true_to_false_without_any_default_value_is_accepted_on_type_layer():
    types = [make_type(1, "Grotte", {"roost_type": SPEC_ROOST})]
    data = pre_load_with_types(types, {"fields": {"roost_type": {"required": False}}})
    assert data["fields"]["roost_type"]["required"] is False


# Règle finale (21/11) : `required` true -> false est lié à la nullabilité ; `store` identique ignoré


def test_nullable_native_is_not_required_by_default_and_can_become_required():
    # (a) recentré (21/11) : un natif nullable est non requis par défaut (required = NOT NULL), donc il
    # n'y a rien à relâcher ; il peut devenir requis (false -> true), et required identique est toléré
    data = pre_load_with_types([], {"fields": {"base_site_description": {"required": True}}})
    assert data["fields"]["base_site_description"]["required"] is True
    data = pre_load_with_types([], {"fields": {"base_site_description": {"required": False}}})
    assert data["fields"]["base_site_description"]["required"] is False


def test_required_false_on_not_null_native_requires_default_value():
    # (b) base_site_name : NOT NULL (base) : rejeté sans default_value, accepté avec
    with pytest.raises(ValidationError, match="base_site_name"):
        pre_load_with_types([], {"fields": {"base_site_name": {"required": False}}})
    data = pre_load_with_types(
        [], {"fields": {"base_site_name": {"required": False, "default_value": "Sans nom"}}}
    )
    assert data["fields"]["base_site_name"]["default_value"] == "Sans nom"


def test_identical_store_on_native_is_ignored_without_error():
    # (c) id_inventor : store {"type": "user"} identique au natif (qui porte aussi code_list) : ignoré
    data = pre_load_with_types([], {"fields": {"id_inventor": {"store": {"type": "user"}}}})
    # Le store natif est conservé tel quel (code_list compris) : la redéfinition est sans effet
    assert data["fields"]["id_inventor"]["store"] == {
        "type": "user",
        "code_list": "__MODULE.CODE_OBSERVERS_LIST",
    }


def test_different_store_on_native_is_rejected():
    # (d) store différent : rejeté
    with pytest.raises(ValidationError, match="id_inventor"):
        pre_load_with_types([], {"fields": {"id_inventor": {"store": {"type": "module"}}}})


def test_identical_store_on_type_field_is_ignored():
    # (e) champ de type : store identique à celui du type : ignoré ; différent : rejeté
    types = [make_type(1, "Grotte", {"roost_type": {**SPEC_ROOST, "store": {"type": "string"}}})]
    data = pre_load_with_types(types, {"fields": {"roost_type": {"store": {"type": "string"}}}})
    assert data["fields"]["roost_type"]["store"] == {"type": "string"}
    with pytest.raises(ValidationError, match="roost_type"):
        pre_load_with_types(types, {"fields": {"roost_type": {"store": {"type": "integer"}}}})


def test_identical_store_on_native_through_type_is_ignored():
    types = [make_type(1, "Grotte", {"id_inventor": {"store": {"type": "user"}}})]
    data = pre_load_with_types(types, {})
    assert data["fields"]["id_inventor"]["store"]["code_list"] == "__MODULE.CODE_OBSERVERS_LIST"


def test_native_required_matches_database_not_null():
    # Cohérence, lecture seule : pour chaque champ natif du site, sauf les exceptions listées, `required`
    # par défaut est vrai si et seulement si la colonne est NOT NULL en base.
    import sqlalchemy as sa
    from sqlalchemy import text

    from geonature.utils.env import db
    from gn_module_monitoring.monitoring.models import TMonitoringSites

    exceptions = {  # ni colonne saisie : PK, uuid, relations, expressions dynamiques
        "id_base_site", "uuid_base_site", "types_site", "medias", "last_visit", "nb_visits",
        "nb_individuals",
    }
    not_null_in_db = {
        name
        for name, nullable in db.session.execute(
            text(
                "select column_name, is_nullable from information_schema.columns "
                "where table_schema = 'gn_monitoring' and table_name in ('t_base_sites', 't_site_complements')"
            )
        ).all()
        if nullable == "NO"
    }
    native = SiteEntityConfigSchema.default_config["fields"]
    columns = sa.inspect(TMonitoringSites).columns
    mismatches = []
    for name, spec in native.items():
        if name in exceptions or name not in not_null_in_db or not isinstance(columns.get(name), sa.Column):
            continue
        if bool(spec.get("required", False)) != (name in not_null_in_db):
            mismatches.append(name)
    assert mismatches == []
