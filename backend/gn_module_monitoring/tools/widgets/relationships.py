from marshmallow import fields, pre_load, validate

from .core import BaseWidget


class NomenclatureWidget(BaseWidget):
    key = "nomenclature"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multi_select = fields.Boolean(load_default=False)

    def _get_default_store(self, data, **kwargs):
        from ..stores import NomenclatureStore, NomenclaturesStore

        # Clés acceptées par le store (multi_select est une option du widget)
        data = {
            k: v
            for k, v in data.items()
            if k in ("nomenclature_type", "cd_nomenclatures", "storage_col", "storage_cols")
        }
        if self["multi_select"]:
            return NomenclaturesStore(data, **kwargs)
        return NomenclatureStore(data, **kwargs)

    def get_api_type(self):
        if self["multi_select"]:
            return list[int]
        return int


class TaxonomyWidget(BaseWidget):
    key = "taxonomy"

    class ConfigSchema(BaseWidget.ConfigSchema):
        id_list = fields.Int(allow_none=True)  # liste TaxHub restreignant la recherche (None = pas de restriction), lue par pnx-taxonomy
        application = fields.String()
        api = fields.String()
        keyValue = fields.String()
        keyLabel = fields.String()
        multiple = fields.Boolean()

    def _get_default_store(self, data, **kwargs):
        from ..stores import TaxonomyStore

        return TaxonomyStore(data, **kwargs)

    def get_api_type(self):
        return int


class DatasetWidget(BaseWidget):
    key = "dataset"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multi_select = fields.Boolean(load_default=False)
        module_code = fields.Str()  # lu par dynamic-form (formDef.module_code)
        creatable_in_module = fields.Str()  # lu par dynamic-form (formDef.creatable_in_module)

    def _get_default_store(self, data, **kwargs):
        from ..stores import DatasetStore, DatasetsStore

        # Clés acceptées par le store (multi_select est une option du widget)
        data = {k: v for k, v in data.items() if k in ("storage_col", "storage_cols")}
        if self["multi_select"]:
            return DatasetsStore(data, **kwargs)
        else:
            return DatasetStore(data, **kwargs)

    def get_api_type(self):
        if self["multi_select"]:
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

        # Clés acceptées par le store (multiple est une option du widget)
        data = {k: v for k, v in data.items() if k in ("storage_col", "storage_cols")}
        if self["multiple"]:
            return ModulesStore(data, **kwargs)
        else:
            return ModuleStore(data, **kwargs)

    def get_api_type(self):
        if self["multiple"]:
            return list[int]
        return int


class HabitatWidget(BaseWidget):
    key = "habitat"

    def _get_default_store(self, data, **kwargs):
        from ..stores import HabitatStore

        return HabitatStore(data, **kwargs)

    def get_api_type(self):
        return int


class IndividualsWidget(BaseWidget):
    key = "individuals"

    class ConfigSchema(BaseWidget.ConfigSchema):
        module_code = fields.Str()  # lu par pnx-individuals (moduleCode)
        id_module = fields.Int()  # module de rattachement (config par défaut du marquage)
        id_list = fields.Int(allow_none=True)  # lu par pnx-individuals (idList)
        cd_nom = fields.Int(allow_none=True)  # lu par pnx-individuals (cdNom)
        bind_all_item = fields.Boolean()  # lu par form.service (objet complet au lieu de l’id)

    def _get_default_store(self, data, **kwargs):
        from ..stores import IndividualStore

        # Clés acceptées par le store (module_code, id_list, cd_nom sont propres au widget)
        return IndividualStore(
            {k: v for k, v in data.items() if k in ("storage_col", "storage_cols")}, **kwargs
        )

    def get_api_type(self):
        return int


class UserWidget(BaseWidget):
    key = "user"

    def _get_default_store(self, data, **kwargs):
        from ..stores import UserStore

        return UserStore(data, **kwargs)

    def get_api_type(self):
        return int


# TODO: observers is a spetial case of user
class ObserversWidget(BaseWidget):
    key = "observers"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multi_select = fields.Boolean(load_default=False)
        multiple = fields.Boolean()  # alias de multi_select (legacy)
        code_list = fields.String()  # liste d'observateurs (code), lue par pnx-observers
        id_list = fields.Raw()  # liste d'observateurs (id), lue par pnx-observers

        @pre_load
        def retrocompat_multiple(self, data, **kwargs):
            if "multiple" in data and "multi_select" not in data:
                data["multi_select"] = data["multiple"]
            return data

    def _get_default_store(self, data, **kwargs):
        from ..stores import UserStore, UsersStore

        # Clés acceptées par le store (multi_select, multiple, id_list sont propres au widget)
        data = {k: v for k, v in data.items() if k in ("storage_col", "storage_cols", "code_list")}
        if self["multi_select"]:
            return UsersStore(data, **kwargs)
        return UserStore(data, **kwargs)

    def get_api_type(self):
        if self["multi_select"]:
            return list[int]
        return int


class AreasWidget(BaseWidget):
    key = "areas"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multiple = fields.Boolean(load_default=False)  # lue par pnx-areas

    def _get_default_store(self, data, **kwargs):
        from ..stores import AreaStore, AreasStore

        # Clés acceptées par le store (multiple est une option du widget)
        if self["multiple"]:
            return AreasStore(
                {k: v for k, v in data.items() if k in ("area_code", "storage_col", "storage_cols")},
                **kwargs,
            )
        return AreaStore(
            {k: v for k, v in data.items() if k in ("storage_col", "storage_cols")}, **kwargs
        )

    def get_api_type(self):
        return list[int] if self["multiple"] else int


class MunicipalitiesWidget(BaseWidget):
    key = "municipalities"

    class ConfigSchema(BaseWidget.ConfigSchema):
        multiple = fields.Boolean(load_default=False)

    def _get_default_store(self, data, **kwargs):
        from ..stores import AreasStore

        return AreasStore({**data, "area_code": "COM"}, **kwargs)

    def get_api_type(self):
        return list[int] if self["multiple"] else int


# TODO: checkbox, radio, html, bool_checkbox, multiselect, observers-text, media, medias, date, text, textarea, jsonb, time
