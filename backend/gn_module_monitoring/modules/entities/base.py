from collections import UserDict
from copy import deepcopy
import json
from functools import cache
from typing import ClassVar

import sqlalchemy as sa
import marshmallow as ma
from marshmallow import ValidationError

from geonature.utils.env import db

from gn_module_monitoring.config.utils import apply_substitutions, monitoring_module_config_path
from gn_module_monitoring.tools.utils import schema_context

ENTITY_MAP: dict[str, type] = {}

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

    @property
    def config_path(self):
        return monitoring_module_config_path(self.module.module_code) / f"{self.name}.json"

    def __init__(self, monitoring_module):
        super().__init__()
        self.module = monitoring_module
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
