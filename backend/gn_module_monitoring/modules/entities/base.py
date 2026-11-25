from collections import UserDict
from copy import deepcopy
import datetime
import json
import os
import uuid
from functools import cache
from typing import ClassVar
from zoneinfo import ZoneInfo

import sqlalchemy as sa
import marshmallow as ma
from sqlalchemy.orm import RelationshipProperty
from cel_expr_python.cel import Type
from google.protobuf.timestamp_pb2 import Timestamp
from flask import current_app
from marshmallow import ValidationError, validates_schema

from geonature.utils.env import db

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.tools.cel import _CEL_SKIP, value_to_cel
from gn_module_monitoring.tools.stores import DummyStore
from gn_module_monitoring.tools.stores.type import GeometryStore
from gn_module_monitoring.tools.utils import schema_context

ENTITY_MAP: dict[str, type] = {}


class StoreAccessMixin:
    """
    Accès au store de chaque champ d'un schéma étendu. `field_stores` (nom du champ -> store) vient de la
    configuration de l'entité : il couvre les champs natifs (hérités du schéma de base, quel que soit leur
    type marshmallow) comme les champs additionnels. Le sous-schéma `data` a son propre mapping, que
    `store_of` consulte aussi.
    """

    field_stores: ClassVar[dict] = {}

    def store_of(self, name):
        """Store du champ `name` (None si le champ n'est pas configuré)."""
        if name in self.field_stores:
            return self.field_stores[name]
        data_field = self.fields.get("data")
        if data_field is not None:
            return data_field.schema.store_of(name)
        return None


class ExtraDataMixin:
    """
    Schéma avec des champs supplémentaires, stockés dans la clé `data` du modèle.
    Les champs supplémentaires sont envoyés à plat par l’API.
    """

    extra_field_names: frozenset = frozenset()

    @ma.pre_load
    def collect_extra_fields(self, data, **kwargs):
        # Déplace à plat dans `data` les champs supplémentaires.
        # La validation sera faite par extra_data_schema`
        data = dict(data)  # swallow copy to avoide side effect
        extra_data = {}
        for name in self.extra_field_names:
            if name in data:
                extra_data[name] = data.pop(name)
        data["data"] = extra_data
        return data

    @ma.post_dump
    def flatten_extra_fields(self, data, **kwargs):
        # Remonte à la racine les champs supplémentaires sérialisés dans `data`
        extra = data.pop("data", None) or {}
        for name in self.extra_field_names:
            data[name] = extra.get(name)
        return data

    def _to_storage(self, data: dict) -> dict:
        """
        Valeurs chargées (sorties des champs des stores) converties pour le modèle, par le store de chaque
        champ : un champ natif va vers `to_native_storage` (ex. PK pour une FK colonne), un champ additionnel va vers
        `to_json_storage` (valeur stockée dans `data`).
        """
        extra = data.get("data") or {}
        # Un champ sans store (ex. medias, champs calculés) n'a pas de conversion : sa valeur est gardée
        converted = {
            name: (
                self.field_stores[name].to_native_storage(value) if name in self.field_stores else value
            )
            for name, value in data.items()
            if name != "data" and name not in self.extra_field_names
        }
        converted["data"] = {
            name: self.field_stores[name].to_json_storage(value) for name, value in extra.items()
        }
        return converted

    @ma.post_load
    def make_instance(self, data, **kwargs):
        # Mise à jour : les champs déclarés absents de la requête sont supprimés, mais les données
        # stockées qui ne sont pas déclarées dans la configuration sont conservées.
        data = self._to_storage(data)
        instance = (self.instance or self.get_instance(data)) if self._load_instance else None
        if instance is not None:
            kept = {
                name: value
                for name, value in (instance.data or {}).items()
                if name not in self.extra_field_names
            }
            data["data"] = {**kept, **(data.get("data") or {})}
        return super().make_instance(data, **kwargs)


class CELMixin:
    """
    Schéma dont les champs peuvent avoir des conditions CEL, évaluées sur l’ensemble des champs :
    - `required_cel` : si elle est vraie et que la valeur est absente, le champ est en erreur ;
    - `validate_cel` : si la valeur est présente, chaque condition doit être vraie, sinon le
      champ est en erreur avec le message de la condition ;
    - `entity_validate_cel` : conditions sur l’objet entier, en erreur sous la clé `_schema`.
    """

    # Expressions compilées au chargement de la configuration (voir compile_entity_cel_expressions)
    compiled_required_cel: ClassVar[dict] = {}
    compiled_validate_cel: ClassVar[dict] = {}
    entity_validate_cel: ClassVar[list] = []

    def _field_value(self, name, data, extra):
        return extra.get(name) if name in self.extra_field_names else data.get(name)

    def _cel_value(self, name, value):
        """Valeur CEL d'un champ : convertie par son store (`BaseStore.to_cel`)."""
        store = self.store_of(name)
        return value_to_cel(value) if store is None else store.to_cel(value)

    @validates_schema
    def check_cel(self, data, **kwargs):
        # Exécuté après la désérialisation de tous les champs, et avant post_load (création de
        # l’instance) : le contexte CEL contient tous les champs, natifs et supplémentaires.
        extra = data.get("data") or {}
        context = {}
        for name in {*self.fields, *self.extra_field_names} - {"data"}:
            value = self._cel_value(name, self._field_value(name, data, extra))
            if value is not _CEL_SKIP:
                context[f"fields.{name}"] = value

        errors = {}

        def evaluate(name, expression):
            try:
                result = expression.eval(data=context)
            except RuntimeError as e:
                errors.setdefault(name, []).append(f"Expression CEL impossible à évaluer : {e}")
                return None
            if result.type() != Type.BOOL:
                errors.setdefault(name, []).append(
                    f"Expression CEL non booléenne : {result.value()}"
                )
                return None
            return result.value()

        for name, expression in self.compiled_required_cel.items():
            if self._field_value(name, data, extra) is None and evaluate(name, expression):
                errors.setdefault(name, []).append("Champ requis.")
        for name, conditions in self.compiled_validate_cel.items():
            if self._field_value(name, data, extra) is None:
                continue
            for expression, message in conditions:
                if evaluate(name, expression) is False:
                    errors.setdefault(name, []).append(message)
        for expression, message in self.entity_validate_cel:
            if evaluate("_schema", expression) is False:
                errors.setdefault("_schema", []).append(message)

        native_errors = {n: m for n, m in errors.items() if n not in self.extra_field_names}
        extra_errors = {n: m for n, m in errors.items() if n in self.extra_field_names}
        if errors:
            raise ValidationError(
                {**native_errors, **({"data": extra_errors} if extra_errors else {})}
            )


class BaseEntity(UserDict):
    name: ClassVar[str | None] = None
    model: ClassVar[type[db.Model]] = None  # type: ignore
    model_schema_class: ClassVar[type[ma.Schema]] = None  # type: ignore
    config_schema_class: ClassVar[type[ma.Schema]] = None  # type: ignore
    import_actions_class: ClassVar[type | None] = None  # classe d'actions d'import de l'entité

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.name is not None:
            ENTITY_MAP[cls.name] = cls

    @classmethod
    @cache
    def get_model_attrs(cls):
        return sa.inspect(cls.model).attrs

    @classmethod
    def get_model_schema(cls):
        return cls.model_schema_class()

    def get_extended_schema(self, *mixins):
        """
        Schéma du modèle étendu avec les champs supplémentaires, stockés dans la colonne `data`.
        Un champ est supplémentaire si son store n’est pas lié à une colonne du modèle.
        """
        if mixins not in self._extended_schemas:
            self._extended_schemas[mixins] = self._build_extended_schema(mixins)
        return self._extended_schemas[mixins]

    def _build_extra_data_schema(self, extra_stores):
        """
        Schéma de la colonne `data`, qui contient les champs supplémentaires non-natifs.
        - Les champs valident et convertissent la valeur de l’API en valeur Python (chargement) ;
        - la conversion en valeur stockable (`to_json_storage`) est faite par le schéma principal (make_instance) ;
        - pre_dump convertit les valeurs lues en JSON en PK (`from_json_storage`) avant que
          les champs ne les envoient telles quelles à l’API.
        """

        def convert_from_storage(self, data, **kwargs):
            # Une clé absente de la configuration (champ supprimé) est conservée telle quelle
            return {
                name: extra_stores[name].from_json_storage(value) if name in extra_stores else value
                for name, value in data.items()
            }

        extra_fields = {name: store.get_field() for name, store in extra_stores.items()}
        return type(
            f"{type(self).__name__}ExtraDataSchema",
            (ma.Schema, StoreAccessMixin),
            {
                **extra_fields,
                "field_stores": dict(extra_stores),
                "convert_from_storage": ma.pre_dump(convert_from_storage),
            },
        )

    def patch_payload(self, instance, post_data: dict, only: list) -> dict:
        """
        Données d'une mise à jour partielle (PATCH), ramenées à une fiche complète : l'état courant de
        l'instance (même représentation que l'API) est complété par les champs envoyés. La validation
        (champs requis, CEL, post_load) porte ainsi toujours sur l'état complet de l'objet, comme à la création.
        """
        current = self.get_extended_schema()(only=only).dump(instance)
        return {**current, **post_data}

    def _build_extended_schema(self, mixins):
        """
        Schéma de validation fondé sur self.model_schema_class, mais ajoutant les champs déclarés
        par la configuration de l’entité. Les champs additionnels non-natifs sont déplacé dans
        un dict "data" par ExtraDataMixin, et sont validés par son propre schéma créé via
        _build_extra_data_schema.
        """
        extra_stores = {
            name: field["store"]
            for name, field in self.data["fields"].items()
            if field["store"].native_attr is None and not isinstance(field["store"], DummyStore)
        }

        extra_data_schema = self._build_extra_data_schema(extra_stores)
        fields = self.data["fields"]
        # TODO: utiliser que les fields fournis par les stores, y compris pour les champs natifs,
        # plutôt que d’hériter du schema de base ?
        # Géométries : on override avec le champ lié au store, qui lit le format d'entrée (`geometry_format`) (WKT dans l’import)
        # Relations natives (ex. observers de la visite) : le champ du store charge les objets, que les CEL
        # et la validation utilisent (API et import). Les géométries lisent leur format d'entrée (`geometry_format`).
        native_store_fields = {
            name: field["store"].get_field()
            for name, field in fields.items()
            if field["store"].native_attr is not None and not isinstance(field["store"], DummyStore)
        }
        attrs = {
            **native_store_fields,
            "extra_field_names": frozenset(extra_stores),
            "field_stores": {name: field["store"] for name, field in fields.items()},
            "compiled_required_cel": {
                name: field["compiled_required_cel"]
                for name, field in fields.items()
                if field["compiled_required_cel"] is not None
            },
            "compiled_validate_cel": {
                name: field["compiled_validate_cel"]
                for name, field in fields.items()
                if field["compiled_validate_cel"]
            },
            "entity_validate_cel": self.data["compiled_validate_cel"],
            "data": ma.fields.Nested(extra_data_schema, allow_none=True, unknown=ma.INCLUDE),
        }

        return type(
            f"{type(self).__name__}ExtendedSchema",
            (
                *mixins,
                ExtraDataMixin,
                CELMixin,
                StoreAccessMixin,
                self.model_schema_class,
            ),  # FIXME: doit-on vraiment utiliser ce schema ?
            attrs,
        )

    @property
    def config_path(self):
        return monitoring_module_config_path(self.module.module_code) / f"{self.name}.json"

    def __init__(self, monitoring_module):
        super().__init__()
        self.module = monitoring_module
        self._extended_schemas = {}
        config_path = self.config_path
        if config_path.is_file():
            with config_path.open() as f:
                config = json.load(f)
        else:
            config = {}

        self.config_schema = self.config_schema_class()
        # Strict : clé inconnue rejetée. Souple : conservée (INCLUDE), voir LOTS.md section 8.
        unknown = ma.RAISE if current_app.config[MODULE_CODE]["STRICT"] else ma.INCLUDE
        with schema_context(entity=self):
            self.data = self.config_schema.load(config, unknown=unknown)

    def extra_fields(self):
        """
        Champs non natifs de l'entité (store sans `native_attr`, stockés dans `data`).
        """
        return {
            name: field
            for name, field in self.data["fields"].items()
            if field["store"].native_attr is None
        }

    def dump_config(self):
        return self.config_schema.dump(self.data)
