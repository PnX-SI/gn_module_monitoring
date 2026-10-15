from marshmallow import fields, validate

from .core import BaseWidget


class NomenclatureWidget(BaseWidget):
    key = "nomenclature"

    def _get_default_store(self, data, **kwargs):
        from ..stores import NomenclatureStore

        return NomenclatureStore(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyWidget(BaseWidget):
    key = "taxonomy"

    def _get_default_store(self, data, **kwargs):
        from ..stores import TaxonomyStore

        return TaxonomyStore(data, **kwargs)

    def get_wire_type(self):
        return int


class DatasetWidget(BaseWidget):
    key = "dataset"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multi_select = fields.Boolean(load_default=False)

    def _get_default_store(self, data, **kwargs):
        from ..stores import DatasetStore, DatasetsStore

        # multi_select est une option du widget, pas du store
        data = {k: v for k, v in data.items() if k != "multi_select"}
        if self.config["multi_select"]:
            return DatasetsStore(data, **kwargs)
        else:
            return DatasetStore(data, **kwargs)

    def get_wire_type(self):
        if self.config["multi_select"]:
            return list[int]
        return int


class ModuleWidget(BaseWidget):
    key = "module"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multiple = fields.Boolean(load_default=False)
        keyValue = fields.Str(load_default="id_module")
        keyLabel = fields.Str(load_default="module_label")
        api = fields.Str(load_default="monitorings/modules")

    def _get_default_store(self, data, **kwargs):
        from ..stores import ModuleStore, ModulesStore

        # multiple est une option du widget, pas du store
        data = {k: v for k, v in data.items() if k != "multiple"}
        if self.config["multiple"]:
            return ModulesStore(data, **kwargs)
        else:
            return ModuleStore(data, **kwargs)

    def get_wire_type(self):
        if self.config["multiple"]:
            return list[int]
        return int


class HabitatWidget(BaseWidget):
    key = "habitat"

    def _get_default_store(self, data, **kwargs):
        from ..stores import HabitatStore

        return HabitatStore(data, **kwargs)

    def get_wire_type(self):
        return int


class UserWidget(BaseWidget):
    key = "user"

    def _get_default_store(self, data, **kwargs):
        from ..stores import UserStore

        return UserStore(data, **kwargs)

    def get_wire_type(self):
        return int


# TODO: observers is a spetial case of user
class ObserversWidget(BaseWidget):
    key = "observers"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multi_select = fields.Boolean(load_default=False)

    def _get_default_store(self, data, **kwargs):
        from ..stores import UserStore, UsersStore

        # multi_select est une option du widget, pas du store
        data = {k: v for k, v in data.items() if k != "multi_select"}
        # TODO: pass some parameters like the observer list
        if self.config["multi_select"]:
            return UsersStore(data, **kwargs)
        return UserStore(data, **kwargs)

    def get_wire_type(self):
        if self.config["multi_select"]:
            return list[int]
        return int


class AreasWidget(BaseWidget):
    key = "areas"

    class ConfigSchema(BaseWidget.ConfigSchema):
        type = fields.Str(validate=validate.OneOf(["area", "areas"]))

    def _get_default_store(self, data, **kwargs):
        from ..stores import AreasStore

        return AreasStore(data, **kwargs)

    def get_wire_type(self):
        return list[int]


class MunicipalitiesWidget(BaseWidget):
    key = "municipalities"

    def _get_default_store(self, data, **kwargs):
        from ..stores import AreasStore

        return AreasStore({**data, "area_code": "COM"}, **kwargs)

    def get_wire_type(self):
        return list[int]


# TODO: checkbox, radio, html, bool_checkbox, multiselect, observers-text, media, medias, date, text, textarea, jsonb, time, individuals
