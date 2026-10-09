from typing import Any, Literal, Never, Any

from numpy import require

import marshmallow as ma
from marshmallow import fields, validates_schema, ValidationError

from .utils import ValueLabelField


class BaseWidget:
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        attribut_label = fields.String()  # FIXME: required?

    @classmethod
    def get_config_schema_class(cls):
        return cls.ConfigSchema

    def __init__(self, data=None, **kwargs):
        data = data or {}
        if "type_widget" in data:
            self.extra_data = data
            # retro-compat.
            kwargs["unknown"] = ma.EXCLUDE
        else:
            self.extra_data = None
        self.config = self.get_config_schema_class()().load(data, **kwargs)

    def get_default_adapter(self, data=None, **kwargs):
        # Gestion de la rétro-compat: si le widget a été initialisé en mode retro-compat.,
        # on initialise l’adapter en mode retro-compat.
        data = data or {}
        if self.extra_data:
            return self._get_default_adapter(
                {**self.extra_data, **data},
                **{**kwargs, "unknown": ma.EXCLUDE},
            )
        else:
            return self._get_default_adapter(data, **kwargs)

    def _get_default_adapter(self, data, **kwargs):
        raise NotImplementedError

    def get_wire_type(self) -> Any:
        return Never

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class TextWidget(BaseWidget):
    key = "text"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class TextareaWidget(BaseWidget):
    key = "textarea"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class CheckboxWidget(BaseWidget):
    key = "bool_checkbox"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import BooleanAdapter

        return BooleanAdapter(data, **kwargs)

    def get_wire_type(self):
        return bool


class RadioWidget(BaseWidget):
    key = "radio"

    def _get_default_adapter(self, data=None, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class NumberWidget(BaseWidget):
    key = "number"

    class ConfigSchema(BaseWidget.ConfigSchema):
        step = fields.Float()
        min = fields.Float()
        max = fields.Float()

    @property
    def is_integer(self):
        step = self.config.get("step")
        return step is not None and step.is_integer()

    def _get_default_adapter(self, data=None, **kwargs):
        if self.is_integer:
            from .adapters import IntegerAdapter

            return IntegerAdapter(data, **kwargs)
        else:
            from .adapters import FloatAdapter

            return FloatAdapter(data, **kwargs)

    def get_wire_type(self):
        if self.is_integer:
            return int
        else:
            return float


class DateWidget(BaseWidget):
    key = "date"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import DateAdapter

        return DateAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class TimeWidget(BaseWidget):
    key = "time"

    def _get_default_adapter(self, data, **kwargs):
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

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import ValueAdapter

        return ValueAdapter({"values": self.config["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return Literal[tuple(value["value"] for value in self.config["values"])]


class MultiselectWidget(BaseWidget):
    key = "multiselect"

    class ConfigSchema(BaseWidget.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import ListAdapter

        return ListAdapter({"values": self.config["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self.config["values"])]]


class DatalistWidget(BaseWidget):
    key = "datalist"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multiple = fields.Bool(load_default=False)
        values = fields.List(
            fields.Nested(
                ma.Schema.from_dict(
                    {
                        "value": fields.String(required=True),
                        "label": fields.String(required=True),
                    }
                )
            )
        )
        api = fields.String()
        keyValue = fields.String()
        keyLabel = fields.String()

        @validates_schema
        def validates_schema(self, data, **kwargs):
            if "api" in data:
                if "keyValue" not in data:
                    raise ValidationError(
                        {"keyValue": "Avec 'api', vous devez fournir 'keyValue'"}
                    )
                if "keyLabel" not in data:
                    raise ValidationError(
                        {"keyValue": "Avec 'api', vous devez fournir 'keyLabel'"}
                    )

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import StringAdapter

        # This is pure guessing as we do not know the API return type
        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        # We do not know the type returned by the API…
        return Any


class NomenclatureWidget(BaseWidget):
    key = "nomenclature"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import NomenclatureAdapter

        return NomenclatureAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyWidget(BaseWidget):
    key = "taxonomy"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import TaxonomyAdapter

        return TaxonomyAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class DatasetWidget(BaseWidget):
    key = "dataset"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import DatasetAdapter

        return DatasetAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class HabitatWidget(BaseWidget):
    key = "habitat"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import HabitatAdapter

        return HabitatAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class ObserversWidget(BaseWidget):
    key = "observers"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import UserAdapter

        # TODO: pass some parameters like the observer list or multiple
        return UserAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class ObserversTextWidget(BaseWidget):
    key = "observers-text"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import StringAdapter

        return StringAdapter(data, **kwargs)

    def get_wire_type(self):
        return str


class MediaWidget(BaseWidget):
    key = "medias"

    def _get_default_adapter(self, data, **kwargs):
        from .adapters import DummyAdapter

        return DummyAdapter(data, **kwargs)

    def get_wire_type(self):
        return Never


# TODO: checkbox, radio, html, bool_checkbox, number, multiselect, observers, observers-text, media, medias, date, nomenclature, datalist, text, textarea, jsonb, time, taxonomy, site, individuals, dataset, municipalities, areas
# Multiple: multiselect, checkbox, municipalities, areas
