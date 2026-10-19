from collections import UserDict
from copy import deepcopy
import json
from functools import cache
from typing import ClassVar

import sqlalchemy as sa
import marshmallow as ma
from marshmallow import ValidationError

from geonature.utils.env import db

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.tools.stores import DummyStore
from gn_module_monitoring.tools.utils import schema_context

ENTITY_MAP: dict[str, type] = {}


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
            "data": ma.fields.Nested(extra_data_schema, allow_none=True, unknown=ma.INCLUDE),
        }

        return type(
            f"{type(self).__name__}ExtendedSchema",
            (*mixins, ExtraDataMixin, self.model_schema_class),
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
            try:
                self.data = self.config_schema.load(config)
            except ValidationError as e:
                raise ValidationError({self.name: e.messages_dict})

    def dump_config(self):
        return self.config_schema.dump(self.data)
