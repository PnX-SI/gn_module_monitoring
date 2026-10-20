import logging
from typing import ClassVar

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

    class Field(BaseStore.Field):
        # Décodage de la valeur envoyée par l’API, pour les types non JSON (date, uuid…)
        wire_field: ClassVar[fields.Field]

        def _deserialize(self, value, attr, data, **kwargs):
            if self.store.native_attr is not None:
                return self.wire_field.deserialize(value)
            # Champ JSON : la validation seule suffit, la valeur envoyée est conservée
            self.wire_field.deserialize(value)
            return value

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

    class Field(BaseTypeStore.Field):
        wire_type = str

        wire_field = fields.String()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TextWidget

        return TextWidget(data, **kwargs)


class BooleanStore(BaseTypeStore):
    key = "bool"
    sql_type = sa.types.Boolean

    class Field(BaseTypeStore.Field):
        wire_type = bool

        wire_field = fields.Boolean()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import BoolCheckboxWidget

        return BoolCheckboxWidget(data, **kwargs)


class IntegerStore(BaseTypeStore):
    key = "integer"
    sql_type = sa.types.Integer

    class Field(BaseTypeStore.Field):
        wire_type = int

        wire_field = fields.Integer(strict=True)

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NumberWidget

        return NumberWidget({"step": 1}, **kwargs)


class FloatStore(BaseTypeStore):
    key = "float"
    sql_type = sa.types.Float

    class Field(BaseTypeStore.Field):
        wire_type = float

        wire_field = fields.Float()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NumberWidget

        return NumberWidget(data, **kwargs)


class DateStore(BaseTypeStore):
    key = "date"
    sql_type = sa.types.Date

    class Field(BaseTypeStore.Field):
        wire_type = str

        wire_field = fields.Date()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DateWidget

        return DateWidget(data, **kwargs)


class DateTimeStore(BaseTypeStore):
    key = "datetime"
    sql_type = sa.types.DateTime

    class Field(BaseTypeStore.Field):
        wire_type = str

        wire_field = fields.DateTime()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TimeWidget

        return TimeWidget(data, **kwargs)


class UUIDStore(BaseTypeStore):
    key = "uuid"
    sql_type = sa.types.Uuid

    class Field(BaseTypeStore.Field):
        wire_type = str

        wire_field = fields.UUID()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TextWidget

        return TextWidget(data, **kwargs)
