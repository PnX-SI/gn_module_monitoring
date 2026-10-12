from typing import Never

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
