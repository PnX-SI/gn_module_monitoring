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
from flask import current_app
from marshmallow import ValidationError, validates_schema

from geonature.utils.env import db

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.command.imports.constant import ID_FIELD_NAME
from gn_module_monitoring.tools.stores import DummyStore
from gn_module_monitoring.tools.utils import schema_context

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

    @ma.post_load
    def make_instance(self, data, **kwargs):
        # Mise à jour : les champs déclarés absents de la requête sont supprimés, mais les données
        # stockées qui ne sont pas déclarées dans la configuration sont conservées.
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

    @validates_schema
    def check_cel(self, data, **kwargs):
        # Exécuté après la désérialisation de tous les champs, et avant post_load (création de
        # l’instance) : le contexte CEL contient tous les champs, natifs et supplémentaires.
        extra = data.get("data") or {}
        context = {}
        for name in {*self.fields, *self.extra_field_names} - {"data"}:
            value = to_cel_value(self._field_value(name, data, extra))
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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.name is not None:
            ENTITY_MAP[cls.name] = cls

    @classmethod
    def get_import_column_name(cls, field_name: str) -> str | None:
        """
        Nom d'import (`name_field` de bib_fields, `s__kind`, `v__meteo`, ...) du champ `field_name`
        de la configuration de l'entité.

        - l'identifiant de l'entité (ID_FIELD_NAME) garde son nom nu ;
        - les autres champs sont préfixés : `g__` (sites_group), `d__` (observation_detail),
          sinon la première lettre du nom de l'entité.
        Cette règle ne consulte pas IGNORED_IMPORT_FIELDS : un champ exclu de l'import est filtré
        par l'appelant (`build_field_names`). Un champ synthétique dont le nom ne suit pas la règle
        porte un `import_name` explicite (command/imports/protocol.py).
        """
        if field_name == ID_FIELD_NAME.get(cls.name):
            return field_name
        prefix = {"sites_group": "g", "observation_detail": "d"}.get(cls.name, cls.name[0])
        return f"{prefix}__{field_name}"

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
        - post_load convertit les valeurs Python en valeur stockable en JSON (`to_storage`) ;
        - pre_dump convertit les valeurs lues en JSON en PK (`from_storage`) avant que
          les champs ne les envoient telles quelles à l’API.
        """

        def convert_to_storage(self, data, **kwargs):
            return {
                name: extra_stores[name].to_storage(value) if name in extra_stores else value
                for name, value in data.items()
            }

        def convert_from_storage(self, data, **kwargs):
            # Une clé absente de la configuration (champ supprimé) est conservée telle quelle
            return {
                name: extra_stores[name].from_storage(value) if name in extra_stores else value
                for name, value in data.items()
            }

        extra_fields = {name: store.get_field() for name, store in extra_stores.items()}
        return type(
            f"{type(self).__name__}ExtraDataSchema",
            (ma.Schema,),
            {
                **extra_fields,
                "convert_to_storage": ma.post_load(convert_to_storage),
                "convert_from_storage": ma.pre_dump(convert_from_storage),
            },
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
        fields = self.data["fields"]
        attrs = {
            "extra_field_names": frozenset(extra_stores),
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
        unknown = ma.RAISE if current_app.config[MODULE_CODE]["STRICT"] else ma.EXCLUDE
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
