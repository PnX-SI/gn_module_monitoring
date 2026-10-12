from typing import Never

from marshmallow import fields, validate

from .core import BaseWidget


class NomenclatureWidget(BaseWidget):
    key = "nomenclature"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import NomenclatureAdapter

        return NomenclatureAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyWidget(BaseWidget):
    key = "taxonomy"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import TaxonomyAdapter

        return TaxonomyAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class DatasetWidget(BaseWidget):
    key = "dataset"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import DatasetAdapter

        return DatasetAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class HabitatWidget(BaseWidget):
    key = "habitat"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import HabitatAdapter

        return HabitatAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class UserWidget(BaseWidget):
    key = "user"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import UserAdapter

        return UserAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


# TODO: observers is a spetial case of user
class ObserversWidget(BaseWidget):
    key = "observers"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import UserAdapter

        # TODO: pass some parameters like the observer list or multiple
        return UserAdapter(data, **kwargs)

    def get_wire_type(self):
        return int


class MediaWidget(BaseWidget):
    key = "medias"

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import DummyAdapter

        return DummyAdapter(data, **kwargs)

    def get_wire_type(self):
        return Never


class AreasWidget(BaseWidget):
    key = "areas"

    class ConfigSchema(BaseWidget.ConfigSchema):
        type = fields.Str(validate=validate.OneOf(["area", "areas"]))
        many = fields.Boolean(load_default=True)

    def _get_default_adapter(self, data, **kwargs):
        from ..adapters import AreasAdapter

        return AreasAdapter(data, **kwargs)

    def get_wire_type(self):
        if self.config.many:
            return list[int]
        else:
            return int


# TODO: checkbox, radio, html, bool_checkbox, number, multiselect, observers-text, media, medias, date, text, textarea, jsonb, time, taxonomy, site, individuals, municipalities, areas
# Multiple: multiselect, checkbox, municipalities, areas
