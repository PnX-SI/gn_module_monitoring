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
from cel_expr_python.cel import Type
from google.protobuf.timestamp_pb2 import Timestamp
from marshmallow import ValidationError, validates_schema

from geonature.utils.env import db

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.tools.stores import DummyStore
from gn_module_monitoring.tools.utils import CEL_ENV, schema_context

ENTITY_MAP: dict[str, type] = {}


_CEL_SKIP = object()  # sentinel value


@cache
def get_app_timezone():
    """
    Fuseau horaire de l’application, lu dans la variable d’environnement TZ (UTC par défaut).
    """
    return ZoneInfo(os.environ.get("TZ") or "UTC")


def _to_timestamp(value: datetime.datetime) -> Timestamp:
    timestamp = Timestamp()
    timestamp.FromDatetime(value.astimezone(datetime.timezone.utc))
    return timestamp


def to_cel_value(value):
    """
    Convertit une valeur chargée en valeur CEL. Retourne `_CEL_SKIP` si elle n’est pas représentable
    (instance de modèle, géométrie…).
    """
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, datetime.datetime):  # sous-classe de date : à tester en premier
        if value.tzinfo is None:
            value = value.replace(tzinfo=get_app_timezone())
        return _to_timestamp(value)
    if isinstance(value, datetime.date):
        midnight = datetime.datetime.combine(value, datetime.time(), tzinfo=get_app_timezone())
        return _to_timestamp(midnight)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            converted = to_cel_value(item)
            if converted is _CEL_SKIP:
                return _CEL_SKIP
            items.append(converted)
        return items
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        items = {}
        for key, item in value.items():
            converted = to_cel_value(item)
            if converted is _CEL_SKIP:
                return _CEL_SKIP
            items[key] = converted
        return items
    return _CEL_SKIP


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


def compile_conditions(conditions):
    """
    Compile des conditions `validate_cel` normalisées : liste de (expression compilée, message).
    """
    return [
        (CEL_ENV.compile(condition["condition"], disable_check=True), condition["message"])
        for condition in conditions or []
    ]


class CELMixin:
    """
    Schéma dont les champs peuvent avoir des conditions CEL, évaluées sur l’ensemble des champs :
    - `required_cel` : si elle est vraie et que la valeur est absente, le champ est en erreur ;
    - `validate_cel` : si la valeur est présente, chaque condition doit être vraie, sinon le
      champ est en erreur avec le message de la condition ;
    - `entity_validate_cel` : conditions sur l’objet entier, en erreur sous la clé `_schema`.
    """

    entity_stores: ClassVar[dict] = {}
    entity_validate_cel: ClassVar[list] = []

    @classmethod
    @cache
    def compiled_required_cel(cls):
        return {
            name: CEL_ENV.compile(store.required_cel, disable_check=True)
            for name, store in cls.entity_stores.items()
            if store.required_cel is not None
        }

    @classmethod
    @cache
    def compiled_validate_cel(cls):
        return {
            name: compile_conditions(store.validate_cel)
            for name, store in cls.entity_stores.items()
            if store.validate_cel
        }

    def _field_value(self, name, data, extra):
        return extra.get(name) if name in self.extra_field_names else data.get(name)

    @validates_schema
    def check_cel(self, data, **kwargs):
        # Exécuté après la désérialisation de tous les champs, et avant post_load (création de
        # l’instance) : le contexte CEL contient tous les champs, natifs et supplémentaires.
        extra = data.get("data") or {}
        context = {}
        for name in {*self.fields, *self.extra_field_names} - {"data"}:
            value = to_cel_value(self._field_value(name, data, extra))
            if value is not _CEL_SKIP:
                context[name] = value

        errors = {}

        def evaluate(name, expression):
            result = expression.eval(data=context)
            if result.type() != Type.BOOL:
                errors.setdefault(name, []).append(
                    f"Expression CEL non booléenne : {result.value()}"
                )
                return None
            return result.value()

        for name, expression in self.compiled_required_cel().items():
            if self._field_value(name, data, extra) is None and evaluate(name, expression):
                errors.setdefault(name, []).append("Champ requis.")
        for name, conditions in self.compiled_validate_cel().items():
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
        Schéma de validation de la colonne `data`, qui contient les champs supplémentaires non-natifs.
        """
        extra_fields = {name: store.to_field() for name, store in extra_stores.items()}
        return type(
            f"{type(self).__name__}ExtraDataSchema",
            (ma.Schema,),
            dict(extra_fields),
        )

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
        attrs = {
            "extra_field_names": frozenset(extra_stores),
            "entity_stores": {name: field["store"] for name, field in self.data["fields"].items()},
            "entity_validate_cel": compile_conditions(self.data.get("validate_cel")),
            "data": ma.fields.Nested(extra_data_schema, allow_none=True, unknown=ma.INCLUDE),
        }

        return type(
            f"{type(self).__name__}ExtendedSchema",
            (*mixins, ExtraDataMixin, CELMixin, self.model_schema_class),
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
        with schema_context(entity=self):
            self.data = self.config_schema.load(config)

    def dump_config(self):
        return self.config_schema.dump(self.data)
