from copy import deepcopy
from typing import ClassVar

import marshmallow as ma
from marshmallow import ValidationError, post_load, pre_load

from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.config.entities.fields import (
    EntityFieldConfigSchema,
    handle_retrocompat_field_definition,
)

from .base import BaseEntityConfigSchema


# Clés qu'un protocole ou un type de site peut redéfinir sur un champ déjà défini (type ou natif).
# `store` n'est accepté que s'il est identique à la couche précédente (voir clean_redefinition).
REDEFINITION_KEYS = {"widget", "required", "default_value", "validate_cel"}
# Clés de la couche précédente utilisées pour les contrôles de redéfinition
CHECK_KEYS = ("store", "required", "default_value")

# Attributs du store comparés lors d'une redéfinition (voir store_changes) : les autres clés du store
# (copies de la conversion legacy) ne sont pas comparées.
STORE_ATTRIBUTE_KEYS = {
    "type", "code_list", "id_list", "multiple", "multi_select", "params", "code_nomenclature_type",
    "cd_nomenclatures", "nomenclature_type", "module_code", "area_type_code", "type_codes",
    "value_field_name",
}


def _as_cel_list(value):
    """validate_cel brut (absent, chaîne, objet ou liste) -> liste brute."""
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def _concat_cel(*layers):
    """Concatène les validate_cel bruts des couches, dans l'ordre (natif, type, protocole)."""
    result = []
    for layer in layers:
        result.extend(_as_cel_list(layer))
    return result


def _redefinition_error(field_name, message):
    return ValidationError({"fields": {field_name: [message]}})


def _required_of(spec) -> bool:
    """`required` effectif d'une spécification : un `required` non booléen (valeur dynamique, voir
    EntityFieldConfigSchema) est chargé comme non requis."""
    value = spec.get("required", False)
    return value if isinstance(value, bool) else False


def _layer_info(native, spec):
    """Valeurs de contrôle de la couche courante : celles du natif, puis celles de la spécification."""
    info = {key: native[key] for key in CHECK_KEYS if key in native}
    info.update({key: spec[key] for key in CHECK_KEYS if key in spec})
    return info


def store_changes(previous_store, store):
    """
    Attributs de store (STORE_ATTRIBUTE_KEYS) qui diffèrent de la couche précédente.
    """
    previous_store = previous_store or {}
    return {
        key: value
        for key, value in (store or {}).items()
        if key in STORE_ATTRIBUTE_KEYS and previous_store.get(key) != value
    }


def clean_redefinition(field_name, spec, previous, origin, not_null):
    """
    Vérifie la redéfinition `spec` d'un champ déjà défini, contre la couche `previous`
    (dict des valeurs CHECK_KEYS de la couche précédente). Renvoie la spécification à fusionner.

    - Clés : seules REDEFINITION_KEYS et `store` sont acceptées.
    - `store` : ignoré sans erreur s'il ne change rien par rapport à `previous` ; sinon rejeté.
    - `required` : false -> true toujours autorisé. true -> false rejeté si `not_null` (le natif est
      requis par défaut, donc NOT NULL en base) et qu'aucune `default_value` non None n'est disponible
      (dans le bloc redéfini, sinon dans la couche précédente). Un champ de type n'a pas de colonne :
      relâcher `required` y est toujours autorisé.
    """
    # Seules les clés que le schéma de champ reconnaît peuvent redéfinir quoi que ce soit : une clé
    # inconnue est ignorée au chargement (EXCLUDE), elle n'est donc pas interdite, elle est inerte.
    forbidden = (set(spec) & set(EntityFieldConfigSchema().fields)) - REDEFINITION_KEYS - {"store"}
    if forbidden:
        raise _redefinition_error(
            field_name,
            f"{origin.capitalize()} ne peut redéfinir le champ '{field_name}' que par "
            f"{', '.join(sorted(REDEFINITION_KEYS | {'store'}))} (clé(s) interdite(s) : "
            f"{', '.join(sorted(forbidden))}).",
        )
    cleaned = deepcopy(spec)
    if "store" in cleaned:
        if store_changes(previous.get("store"), cleaned["store"]):
            raise _redefinition_error(
                field_name,
                f"{origin.capitalize()} ne peut modifier le store du champ '{field_name}' "
                "(seul un store identique à celui de la couche précédente est accepté).",
            )
        del cleaned["store"]  # identique : ignoré
    if "required" in cleaned:
        default_value = (
            cleaned["default_value"] if "default_value" in cleaned else previous.get("default_value")
        )
        if _required_of(previous) and not _required_of(cleaned) and not_null and default_value is None:
            raise _redefinition_error(
                field_name,
                f"{origin.capitalize()} ne peut passer le champ '{field_name}' de requis à non "
                "requis sans 'default_value' (colonne NOT NULL).",
            )
    return cleaned


def _apply_protocol_redefinition(merged, protocol_spec):
    """Applique par-dessus le champ de type les clés redéfinies (déjà vérifiées) par le protocole."""
    if "widget" in protocol_spec:
        merged["widget"] = {**merged.get("widget", {}), **deepcopy(protocol_spec["widget"])}
    for key in ("required", "default_value"):
        if key in protocol_spec:
            merged[key] = deepcopy(protocol_spec[key])
    if "validate_cel" in protocol_spec:
        merged["validate_cel"] = _concat_cel(merged.get("validate_cel"), protocol_spec["validate_cel"])
    return merged


class SiteEntityConfigSchema(BaseEntityConfigSchema):
    types_site = ma.fields.Dict(dump_only=True)

    @pre_load
    def pre_load(self, data, **kwargs):
        """
        Fusion statique des champs spécifiques des types de site du module dans les champs du site
        (P1). Ordre de fusion :
        1. les champs des types de site sont ajoutés à la configuration du site, et ont priorité
           sur tout champ de même nom du protocole ;
        2. le protocole peut redéfinir, sur un champ de type ou natif, `widget` et `required` (voir
           `clean_redefinition`) ; `default_value` accompagne le passage à false sur un champ NOT NULL ;
        3. le widget et `required` du protocole s'appliquent par-dessus le champ final.

        Un type de site peut redéfinir un champ natif avec les mêmes clés (widget, required).

        Erreurs de chargement :
        - un même nom défini par deux types avec des spécifications différentes (P2) ;
        - une clé autre que `widget`, `required`, `default_value` sur un champ de type ou natif ;
        - passage de `required` de true à false sans `default_value` (type ou protocole).
        Un même champ, identique, porté par plusieurs types est un champ partagé (comme le legacy).
        """
        native_fields = self.get_default_config()["fields"]
        # Format courant d'abord (rétro-compatibilité convertie), fusion ensuite
        protocol = {
            name: handle_retrocompat_field_definition(spec)
            for name, spec in {**data.pop("specific", {}), **data.get("fields", {})}.items()
        }

        type_fields = {}  # nom -> (spécification convertie, libellé du type qui la définit)
        for ts in schema_context.get()["entity"].module.module.types_site:
            config = ts.config or {}
            label = ts.nomenclature.label_default
            fields = {**config.get("specific", {}), **config.get("fields", {})}
            for field_name, field_spec in fields.items():
                field_spec = handle_retrocompat_field_definition(field_spec)
                if field_name in type_fields and type_fields[field_name][0] != field_spec:
                    other_label = type_fields[field_name][1]
                    raise _redefinition_error(
                        field_name,
                        f"Le champ '{field_name}' est défini différemment par les types "
                        f"de site '{other_label}' et '{label}'.",
                    )
                type_fields.setdefault(field_name, (field_spec, label))

        # Natif -> type -> protocole. Un champ natif est contrôlé contre sa configuration par défaut.
        fields = {name: deepcopy(spec) for name, spec in protocol.items()}
        for field_name, (type_spec, label) in type_fields.items():
            native = native_fields.get(field_name)
            merged = deepcopy(type_spec)
            previous = _layer_info(native or {}, type_spec)
            if native is not None:
                not_null = _required_of(native)
                merged = clean_redefinition(
                    field_name,
                    type_spec,
                    _layer_info(native, {}),
                    f"le type de site '{label}'",
                    not_null,
                )
                if "validate_cel" in type_spec:
                    merged["validate_cel"] = _concat_cel(
                        native.get("validate_cel"), type_spec["validate_cel"]
                    )
                previous = _layer_info(native, merged)
            if field_name in protocol:
                not_null = native is not None and _required_of(native)
                protocol_spec = clean_redefinition(
                    field_name, protocol[field_name], previous, "le protocole", not_null
                )
                merged = _apply_protocol_redefinition(merged, protocol_spec)
            fields[field_name] = merged

        for field_name, field_spec in protocol.items():
            if field_name in type_fields or field_name not in native_fields:
                continue
            native = native_fields[field_name]
            cleaned = clean_redefinition(
                field_name,
                field_spec,
                _layer_info(native, {}),
                "le protocole",
                _required_of(native),
            )
            if "validate_cel" in cleaned:
                cleaned["validate_cel"] = _concat_cel(
                    native.get("validate_cel"), cleaned["validate_cel"]
                )
            fields[field_name] = cleaned
        data["fields"] = fields
        return super().pre_load(data, **kwargs)

    @post_load
    def load_types_site_ids_for_fields(self, data, **kwargs):
        """
        This hook:
            - Add types_site to config.
            - Add id_types_site to all fields which comes from types site.
        """
        data["types_site"] = {}
        for ts in schema_context.get()["entity"].module.module.types_site:
            config = ts.config or {}
            fields = {**config.get("specific", {}), **config.get("fields", {})}
            for field_name in fields:
                data["fields"][field_name].setdefault("id_types_site", []).append(
                    ts.id_nomenclature_type_site
                )
            data["types_site"][ts.id_nomenclature_type_site] = {
                "name": ts.nomenclature.label_default
            }
        return data

    default_config: ClassVar = {
        "chained": True,
        "id_field_name": "id_base_site",
        "description_field_name": "base_site_name",
        "label": "Site",
        "label_list": "Sites",
        "genre": "M",
        "geom_field_name": "geom",
        "uuid_field_name": "uuid_base_site",
        "geometry_type": ["Point", "LineString", "Polygon"],
        "display_properties": [
            "base_site_name",
            "base_site_code",
            "base_site_description",
            "id_inventor",
            "first_use_date",
            "last_visit",
            "nb_visits",
            "altitude_min",
            "altitude_max",
            "types_site",
        ],
        "display_list": [
            "base_site_name",
            "base_site_code",
            "last_visit",
            "id_inventor",
            "nb_visits",
            "types_site",
            "nb_individuals",
        ],
        "sorts": [{"prop": "last_visit", "dir": "desc"}],
        "fields": {
            # Géométrie native (TMonitoringSites.geom, SRID 4326) : GeoJSON en API, WKT en import
            "geom": {
                "store": {
                    "type": "geometry",
                    "geometry_type": ["Point", "LineString", "Polygon"],
                },
                "widget": {"type": "textarea", "attribut_label": "Géométrie (WKT)"},
                "required": True,
            },
            "base_site_code": {
                "widget": {"type": "text", "attribut_label": "Code"},
                "required": False,
            },
            "base_site_name": {
                "widget": {"type": "text", "attribut_label": "Nom"},
                "required": True,
            },
            "base_site_description": {
                "widget": {"type": "textarea", "attribut_label": "Description"},
            },
            "id_inventor": {
                "store": {
                    "type": "user",
                    "code_list": "__MODULE.CODE_OBSERVERS_LIST",
                },
                "widget": {
                    "type": "observers",
                    "attribut_label": "Observateur",
                    "multi_select": False,
                },
                "required": False,
            },
            "id_digitiser": {
                "store": {"type": "user"},
                "widget": {"attribut_label": "Digitiser", "hidden": True},
                "required": False,
            },
            "first_use_date": {
                "store": {"type": "datetime"},
                "widget": {"attribut_label": "Date description"},
                "required": False,
            },
            "last_visit": {
                "widget": {"type": "date", "attribut_label": "Dernière visite", "hidden": True},
            },
            "nb_visits": {
                "widget": {"type": "number", "attribut_label": "Nb. visites", "hidden": True},
            },
            "nb_individuals": {
                "store": {"type": "integer"},
                "widget": {"attribut_label": "Nb. individus", "hidden": True},
            },
            "uuid_base_site": {
                "store": {"type": "uuid"},
                "widget": {"type": "text", "attribut_label": "uuid", "hidden": True},
            },
            "medias": {
                "widget": {
                    "type": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_base_sites",
                },
            },
            "altitude_min": {
                "store": {"type": "integer"},
                "widget": {
                    "attribut_label": "Altitude (min)",
                    "hidden": True,
                },
            },
            "altitude_max": {
                "store": {"type": "integer"},
                "widget": {
                    "attribut_label": "Altitude (max)",
                    "hidden": True,
                },
            },
            "types_site": {
                "store": {"type": "types_site"},
                "widget": {
                    "type": "datalist",
                    "attribut_label": "Type(s) de site",
                    "keyValue": "id_nomenclature_type_site",
                    "keyLabel": "label",
                    "multiple": True,
                    "api": "__MONITORINGS_PATH/modules/__MODULE.MODULE_CODE/types_sites",
                    "application": "GeoNature",
                    "nullDefault": True,
                    "definition": "Permet de n'avoir que les types de site lié au module",
                    "designStyle": "bootstrap",
                },
                "required": True,
            },
        },
    }

    def get_default_config(self):
        entity = schema_context.get()["entity"]
        config = deepcopy(self.default_config)
        if "sites_group" in entity.module.entities_list:
            # si sites_group fait partie du tree, alors site a par défaut un champs id_sites_group d’ajouté
            config["fields"]["id_sites_group"] = {
                "store": {"type": "sites_group"},
                "widget": {
                    "attribut_label": "Groupe de sites",
                    "hidden": True,
                    "keyValue": "id_sites_group",
                    "keyLabel": "sites_group_name",
                    "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/sites_group?id_module=__MODULE.ID_MODULE&fields=id_sites_group&fields=sites_group_name",
                    "application": "GeoNature",
                },
            }
        return config
