import logging

from marshmallow import fields, validate, ValidationError
from flask import current_app

from gn_module_monitoring import MODULE_CODE

from .core import BaseStore

logger = logging.getLogger(__name__)


class BaseRelationshipStore(BaseStore):
    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        if self.native_column is not None:
            columns = self.native_column.columns
            if (
                len(columns) != 1
                or len(fks := columns[0].foreign_keys) != 1
                or next(iter(fks)).target_fullname != self.fk_target
            ):
                error_message = f"Le store {self.key} doit être utilisé avec un champs FK vers {self.fk_target}"
                if current_app.config[MODULE_CODE]["STRICT"]:
                    raise ValidationError({self.field_name: error_message})
                else:
                    logger.warning(f"Validation warning: {error_message}")

    @classmethod
    def is_suitable_for_column(cls, column):
        return (
            len(fks := column.foreign_keys) == 1
            and next(iter(fks)).target_fullname == cls.fk_target
        )


class UserStore(BaseStore):
    key = "user"
    fk_target = "utilisateurs.t_roles.id_role"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("user"))
        multiple = fields.Bool(load_default=False)

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import UserWidget

        return UserWidget(data, **kwargs)

    def get_wire_type(self):
        if self.config["multiple"]:
            return list[int]
        return int


class ObserverListStore(BaseStore):
    key = "observer_list"
    fk_target = "utilisateurs.t_listes.id_liste"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("observer_list"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatalistWidget

        # TODO: instancier DatalistWidget avec les bon paramètres
        raise NotImplementedError("Missing default widget for adapter 'observer_list'")

    def get_wire_type(self):
        return list[int]


class TaxonomyStore(BaseRelationshipStore):
    key = "taxonomy"
    fk_target = "taxonomie.taxref.cd_nom"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("taxonomy"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import TaxonomyWidget

        return TaxonomyWidget(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyListStore(BaseStore):
    key = "taxonomy_list"
    fk_target = "taxonomie.bib_listes.id_liste"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("taxonomy_list"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Liste des taxons",
                "keyValue": "id_liste",
                "keyLabel": "nom_liste",
                "multiple": False,
                "api": "biblistes/",
            },
            **kwargs,
        )

    def get_wire_type(self):
        return int


class DatasetStore(BaseStore):
    key = "dataset"
    fk_target = "gn_commons.t_datasets.id_dataset"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("dataset"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatasetWidget

        return DatasetWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        return int


class HabitatStore(BaseStore):
    key = "habitat"
    fk_target = "taxonomie.taxref.cd_nom"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("habitat"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import HabitatWidget

        return HabitatWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        return int


class AreasStore(BaseStore):
    key = "areas"
    fk_target = "ref_geo.l_areas.id_area"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.OneOf(["area", "areas"]))
        many = fields.Boolean(load_default=True)

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import AreasWidget

        return AreasWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        if self.config["many"]:
            return list[int]
        else:
            return int


class TypesSiteStore(BaseStore):
    key = "types_site"
    fk_target = "gn_commons.bib_nomenclatures.id_nomenclature"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("types_site"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Type(s) de site",
                "keyValue": "id_nomenclature_type_site",
                "keyLabel": "label",
                "multiple": True,
                "api": "__MONITORINGS_PATH/modules/__MODULE.MODULE_CODE/types_sites",
            },
            **kwargs,
        )

    def get_wire_type(self) -> type:
        return int


class ModuleStore(BaseStore):
    key = "module"
    fk_target = "gn_commons.t_modules.id_module"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("module"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Modules",
                "keyValue": "id_module",
                "keyLabel": "module_label",
                "multiple": True,
                "api": "monitorings/modules",
            },
            **kwargs,
        )

    def get_wire_type(self) -> type:
        return list[int]
