from typing import Any, Literal, Never, Any

import marshmallow as ma
from marshmallow import fields

from .utils import ValueLabelField


class BaseWidget:
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

    def __init__(self, data=None, **kwargs):
        self.config = self.ConfigSchema().load(data or {}, **kwargs)

    def get_default_adapter(self, data=None, **kwargs):
        raise NotImplementedError

    def get_wire_type(self) -> Any:
        return Never

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class TextWidget(BaseWidget):
    key = "text"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class TextareaWidget(BaseWidget):
    key = "textarea"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class CheckboxWidget(BaseWidget):
    key = "bool_checkbox"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import BooleanAdapter

        return BooleanAdapter(data, **kwargs)

    def get_wire_type(self):
        return bool


class RadioWidget(BaseWidget):
    key = "radio"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class NumberWidget(BaseWidget):
    key = "number"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import FloatAdapter

        return FloatAdapter(data, **kwargs)

    def get_wire_type(self):
        return float


class DateWidget(BaseWidget):
    key = "date"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import DateAdapter

        return DateAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class TimeWidget(BaseWidget):
    key = "time"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import TimeAdapter

        return TimeAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class SelectWidget(BaseWidget):
    key = "select"

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        values = fields.List(ValueLabelField(), required=True)

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import ValueAdapter

        return ValueAdapter({"values": self.config["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return Literal[tuple(value["value"] for value in self.config["values"])]


class MultiselectWidget(BaseWidget):
    key = "multiselect"

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        values = fields.List(ValueLabelField(), required=True)

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import ListAdapter

        return ListAdapter({"values": self.config["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self.config["values"])]]


class DatalistWidget(BaseWidget):
    key = "datalist"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        # We do not know the type returned by the API…
        return Any


class NomenclatureWidget(BaseWidget):
    key = "nomenclature"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import NomenclatureAdapter

        return NomenclatureAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyWidget(BaseWidget):
    key = "taxonomy"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import TaxonomyAdapter

        return TaxonomyAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class MediaWidget(BaseWidget):
    key = "medias"

    def get_default_adapter(self, data=None, **kwargs):
        from .adapters import DummyAdapter

        return DummyAdapter(data, **kwargs)


# TODO: checkbox, radio, html, bool_checkbox, number, multiselect, observers, observers-text, media, medias, date, nomenclature, datalist, text, textarea, jsonb, time, taxonomy, site, individuals, dataset, municipalities, areas
# Multiple: multiselect, checkbox, municipalities, areas
