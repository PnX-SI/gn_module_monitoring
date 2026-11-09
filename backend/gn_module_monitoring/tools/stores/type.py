import datetime
import logging
import uuid

import sqlalchemy as sa
from flask import current_app
from marshmallow import ValidationError, fields
from sqlalchemy.orm import ColumnProperty

from gn_module_monitoring import MODULE_CODE

from .base import BaseStore

log = logging.getLogger(__name__)


class BaseTypeStore(BaseStore):
    """
    Store pour une colonne simple dont le type SQL correspond à `sql_type`.
    """

    # Le stockage JSON utilise la représentation de l’API (date et uuid sont stockés en chaîne)
    def to_storage(self, value):
        return None if value is None else self.get_field()._serialize(value, None, None)

    def from_storage(self, value):
        return None if value is None else self.get_field().deserialize(value)

    @classmethod
    def is_suitable_for_column(cls, column):
        return isinstance(column.type, cls.sql_type)

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        if self.native_attr is not None:
            # Cas attendu : une colonne simple, dont le type SQL correspond à self.sql_type
            error_message = None
            if (
                not isinstance(self.native_attr, ColumnProperty)
                or len(self.native_attr.columns) != 1
            ):
                error_message = f"Le store {self.key} doit être utilisé avec une colonne simple."
            else:
                column = self.native_attr.columns[0]
                if not self.is_suitable_for_column(column):
                    error_message = (
                        f"Le store {self.key} doit être utilisé avec une colonne de type "
                        f"{self.sql_type.__name__}. Trouvé une colonne de type {column.type}."
                    )
            if error_message is not None:
                if current_app.config[MODULE_CODE]["STRICT"]:
                    raise ValidationError({self.field_name: error_message})
                else:
                    log.warning(f"Validation warning: {error_message}")


class StringStore(BaseTypeStore):
    key = "string"
    sql_type = sa.types.String

    def get_field(self) -> fields.Field:
        return fields.String(**self._get_field_kwargs())

    def get_api_type(self) -> type:
        return str

    def get_python_type(self) -> type:
        return str

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TextWidget

        return TextWidget(data, **kwargs)


class BooleanStore(BaseTypeStore):
    key = "bool"
    sql_type = sa.types.Boolean

    def get_field(self) -> fields.Field:
        return fields.Boolean(**self._get_field_kwargs())

    def get_api_type(self) -> type:
        return bool

    def get_python_type(self) -> type:
        return bool

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import BoolCheckboxWidget

        return BoolCheckboxWidget(data, **kwargs)


class IntegerStore(BaseTypeStore):
    key = "integer"
    sql_type = sa.types.Integer

    def get_field(self) -> fields.Field:
        return fields.Integer(strict=True, **self._get_field_kwargs())

    def get_api_type(self) -> type:
        return int

    def get_python_type(self) -> type:
        return int

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NumberWidget

        return NumberWidget({"step": 1}, **kwargs)


class FloatStore(BaseTypeStore):
    key = "float"
    sql_type = sa.types.Float

    def get_field(self) -> fields.Field:
        return fields.Float(**self._get_field_kwargs())

    def get_api_type(self) -> type:
        return float

    def get_python_type(self) -> type:
        return float

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NumberWidget

        return NumberWidget(data, **kwargs)


class DateStore(BaseTypeStore):
    key = "date"
    sql_type = sa.types.Date

    def get_field(self) -> fields.Field:
        return fields.Date(**self._get_field_kwargs())

    def get_api_type(self) -> type:
        return str

    def get_python_type(self) -> type:
        return datetime.date

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DateWidget

        return DateWidget(data, **kwargs)


class DateTimeStore(BaseTypeStore):
    key = "datetime"
    sql_type = sa.types.DateTime

    def get_field(self) -> fields.Field:
        return fields.DateTime(**self._get_field_kwargs())

    def get_api_type(self) -> type:
        return str

    def get_python_type(self) -> type:
        return datetime.datetime

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TimeWidget

        return TimeWidget(data, **kwargs)


class UUIDStore(BaseTypeStore):
    key = "uuid"
    sql_type = sa.types.Uuid

    def get_field(self) -> fields.Field:
        return fields.UUID(**self._get_field_kwargs())

    def get_api_type(self) -> type:
        return str

    def get_python_type(self) -> type:
        return uuid.UUID

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TextWidget

        return TextWidget(data, **kwargs)
