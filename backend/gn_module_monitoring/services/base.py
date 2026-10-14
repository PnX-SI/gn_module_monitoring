from functools import cache
from typing import ClassVar

import sqlalchemy as sa
import marshmallow as ma

from geonature.utils.env import db


class BaseServiceMeta(type):
    """
    Print the name attribut of the class instead of <class '...'>
    """

    def __repr__(cls) -> str:
        return cls.name


class BaseService(metaclass=BaseServiceMeta):
    name: ClassVar[str | None] = None
    model: ClassVar[type[db.Model]] = None  # type: ignore
    model_schema: ClassVar[type[ma.Schema]] = None  # type: ignore
    config_schema: ClassVar[type[ma.Schema]] = None  # type: ignore

    @classmethod
    @cache
    def get_columns(cls):
        return sa.inspect(cls.model).column_attrs
