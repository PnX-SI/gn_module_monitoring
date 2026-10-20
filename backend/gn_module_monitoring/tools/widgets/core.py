from collections import UserDict
from typing import Any, Literal, Never

import marshmallow as ma
from marshmallow import fields, validates_schema, pre_load, ValidationError, validate

from ..utils import ValueLabelField, schema_context, MultilineStr

WIDGET_MAP: dict[str, type] = {}


class BaseWidget(UserDict):
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        type = fields.Str(required=True)

        hidden = fields.Boolean()
        hidden_js = MultilineStr()
        hidden_cel = fields.Str()

        # required, required_cel & validate_cel are defined at field level
        required_js = MultilineStr()

        attribut_label = fields.String()  # FIXME: required?

        @pre_load
        def set_hidden_js(self, data, **kwargs):
            if "hidden" in data and not isinstance(data["hidden"], bool):
                data["hidden_js"] = data.pop("hidden")
            return data

        @pre_load
        def load_default_type(self, data, **kwargs):
            if "type" not in data:
                data["type"] = schema_context.get()["widget"].key
            return data

        def get_attribute(self, obj, attr, default):
            # default function is based on getattr, which fail
            # for dict when accessing for instance keys or values attr.
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return super().get_attribute(obj, attr, default)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "key" in cls.__dict__:
            WIDGET_MAP[cls.key] = cls

    @property
    def config_schema_class(self):
        return self.ConfigSchema

    def __init__(
        self, data=None, *, required=False, required_cel=None, validate_cel=None, **kwargs
    ):
        super().__init__()
        self.required = required
        self.required_cel = required_cel
        self.validate_cel = validate_cel
        data = data or {}
        if "type_widget" in data:
            self.extra_data = data
            # retro-compat.
            kwargs["unknown"] = ma.EXCLUDE
        else:
            self.extra_data = None
        self.config_schema = self.config_schema_class()
        with schema_context(widget=self, retro_compat=self.extra_data is not None):
            self.data = self.config_schema.load(data, **kwargs)

    def dump_config(self):
        return self.config_schema.dump(self.data)

    def get_default_store(self, data=None, **kwargs):
        # Gestion de la rétro-compat: si le widget a été initialisé en mode retro-compat.,
        # on initialise le store en mode retro-compat.
        data = data or {}
        if self.extra_data:
            return self._get_default_store(
                {**{k: v for k, v in self.extra_data.items() if k != "type"}, **data},
                **{**kwargs, "unknown": ma.EXCLUDE},
            )
        else:
            return self._get_default_store(data, **kwargs)

    def _get_default_store(self, data, **kwargs):
        raise NotImplementedError

    def get_wire_type(self) -> Any:
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class HiddenWidget(BaseWidget):
    """
    Champ non affiché dans le formulaire, mais dont la valeur est conservée et envoyée à l'API.
    Le store est celui de l'attribut natif du modèle si il existe, sinon DummyStore.
    """

    key = "hidden"

    class ConfigSchema(BaseWidget.ConfigSchema):
        hidden = fields.Boolean(validate=validate.Equal(True))

    def _get_default_store(self, data, **kwargs):
        from ..stores import BaseStore, DummyStore

        ctx = schema_context.get()
        attr = ctx["entity"].get_model_attrs().get(ctx["field_name"])
        if attr is not None:
            return BaseStore.get_store_from_attr(attr)(data, **kwargs)
        else:
            return DummyStore(data, **kwargs)

    def get_wire_type(self):
        return self.get_default_store().get_wire_type()


class TextWidget(BaseWidget):
    key = "text"

    def _get_default_store(self, data, **kwargs):
        from ..stores import StringStore

        return StringStore(data, **kwargs)

    def get_wire_type(self):
        return str


class TextareaWidget(BaseWidget):
    key = "textarea"

    def _get_default_store(self, data, **kwargs):
        from ..stores import StringStore

        return StringStore(data, **kwargs)

    def get_wire_type(self):
        return str


class BoolCheckboxWidget(BaseWidget):
    key = "bool_checkbox"

    def _get_default_store(self, data, **kwargs):
        from ..stores import BooleanStore

        return BooleanStore(data, **kwargs)

    def get_wire_type(self):
        return bool


class CheckboxWidget(BaseWidget):
    key = "checkbox"

    class ConfigSchema(BaseWidget.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    def _get_default_store(self, data, **kwargs):
        from ..stores import ListStore

        return ListStore({"values": self["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self["values"])]]


class RadioWidget(BaseWidget):
    key = "radio"

    def _get_default_store(self, data=None, **kwargs):
        from ..stores import StringStore

        return StringStore(data, **kwargs)

    def get_wire_type(self):
        return str


class NumberWidget(BaseWidget):
    key = "number"

    class ConfigSchema(BaseWidget.ConfigSchema):
        step = fields.Float()
        # Il existait des protocoles avec min contenant un script js
        # C’est désormais interdit et il faut traduire en CEL
        min = fields.Float()
        max = fields.Float()

    @property
    def is_integer(self):
        step = self.get("step")
        return step is not None and step.is_integer()

    def _get_default_store(self, data=None, **kwargs):
        if self.is_integer:
            from ..stores import IntegerStore

            return IntegerStore(data, **kwargs)
        else:
            from ..stores import FloatStore

            return FloatStore(data, **kwargs)

    def get_wire_type(self):
        if self.is_integer:
            return int
        else:
            return float


class DateWidget(BaseWidget):
    key = "date"

    def _get_default_store(self, data, **kwargs):
        from ..stores import DateStore

        return DateStore(data, **kwargs)

    def get_wire_type(self):
        return str


class TimeWidget(BaseWidget):
    key = "time"

    def _get_default_store(self, data, **kwargs):
        from ..stores import DateTimeStore

        return DateTimeStore(data, **kwargs)

    def get_wire_type(self):
        return str


class SelectWidget(BaseWidget):
    key = "select"

    class ConfigSchema(BaseWidget.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    def _get_default_store(self, data, **kwargs):
        from ..stores import ValueStore

        return ValueStore({"values": self["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return Literal[tuple(value["value"] for value in self["values"])]


class MultiselectWidget(BaseWidget):
    key = "multiselect"

    class ConfigSchema(BaseWidget.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    def _get_default_store(self, data, **kwargs):
        from ..stores import ListStore

        return ListStore({"values": self["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self["values"])]]


class DatalistWidget(BaseWidget):
    key = "datalist"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multiple = fields.Bool(load_default=False)
        values = fields.List(ValueLabelField())
        api = fields.String()
        keyValue = fields.String()
        keyLabel = fields.String()

        @validates_schema
        def validates_schema(self, data, **kwargs):
            if "api" in data and "values" in data:
                raise ValidationError("'api' et 'values' sont mutuellement exclusif")
            if "api" in data:
                if "keyValue" not in data:
                    raise ValidationError(
                        {"keyValue": "Avec 'api', vous devez fournir 'keyValue'"}
                    )
                if "keyLabel" not in data:
                    raise ValidationError(
                        {"keyValue": "Avec 'api', vous devez fournir 'keyLabel'"}
                    )

    def _get_default_store(self, data, **kwargs):
        if "values" in self:
            from ..stores import ValueStore

            return ValueStore({"values": self["values"], **data}, **kwargs)
        else:
            from ..stores import StringStore

            # This is pure guessing as we do not know the API return type
            return StringStore(data, **kwargs)

    def get_wire_type(self):
        if "values" in self:
            return Literal[tuple(value["value"] for value in self["values"])]
        else:
            # We do not know the type returned by the API…
            return Any


# FIXME: what difference with text widget?
class ObserversTextWidget(BaseWidget):
    key = "observers-text"

    def _get_default_store(self, data, **kwargs):
        from ..stores import StringStore

        return StringStore(data, **kwargs)

    def get_wire_type(self):
        return str


class MediaWidget(BaseWidget):
    key = "medias"

    def _get_default_store(self, data, **kwargs):
        from ..stores import DummyStore

        return DummyStore(data, **kwargs)

    def get_wire_type(self):
        return Never


# TODO: checkbox, radio, html, bool_checkbox, number, multiselect, observers, observers-text, media, medias, date, text, textarea, jsonb, time, taxonomy, site, individuals, municipalities, areas
