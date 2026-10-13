from typing import Literal, Never, Any

import marshmallow as ma
from marshmallow import fields, validate

from ..utils import ValueLabelField


class BaseStore:
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

    @classmethod
    def get_config_schema_class(cls):
        return cls.ConfigSchema

    def __init__(self, data=None, **kwargs):
        data = data or {}
        if "type_util" in data:
            self.extra_data = data
            # retro-compat.
            kwargs["unknown"] = ma.EXCLUDE
        else:
            self.extra_data = None
        self.config = self.get_config_schema_class()().load(data, **kwargs)

    def dump_config(self):
        return self.get_config_schema_class()().dump(self.config)

    def get_default_widget(self, data=None, **kwargs):
        # Gestion de la rétro-compat: si l’adapter a été initialisé en mode retro-compat.,
        # on initialise le widget en mode retro-compat.
        data = data or {}
        if self.extra_data:
            return self._get_default_widget(
                {**self.extra_data, **data},
                **{**kwargs, "unknown": ma.EXCLUDE},
            )
        else:
            return self._get_default_widget(data, **kwargs)

    def _get_default_widget(self, data, **kwargs):
        """
        Widget par défaut pour cet adapteur. Si l’utilisateur ne définie pas de widget dans la config,
        alors ce widget sera utilisé.
        """
        raise NotImplementedError

    def get_wire_type(self) -> type:
        raise NotImplementedError

    def wire_to_storage(self, value: Any) -> Any:
        """
        Fonction de validation des données reçu par l’API.
        En cas d’erreur(s), lever une exception ValidationError.
        Retourne la valeur qui doit être stocké en base.
        """
        raise NotImplementedError

    def storage_to_wire(self, value: Any) -> Any:
        """
        Fonction de déserialisation des données depuis la base avant l’envoi à l’API.
        Sauf cas particulier, la données peut être envoyé telle quelle à l’API.
        """
        return value

    def check_stored_value(self, entity, row_id, field_name, value: Any, fix: bool):
        """
        Cette fonction permet de contrôler les données stockées en base.
        Cela doit être un générateur. Chaque valeur qui est yield est comptabilisé comme une erreur.
        Note : il est possible de yield des strings qui commence par "\n", auquel cas il s’agit d’un
               commentaire sur l’erreur précédente et non une nouvelle erreur.
        Si fix est vrai, la fonction est encouragé à proposer des corrections à l’utilisateur.
        Si la fonction retourne une valeur différente de celle reçu en entrée, cela est considéré comme
        une correction et la base sera mise à jour avec la donnée renvoyé.
        """
        yield
        return value

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class DummyStore(BaseStore):
    """
    Cet apapter est utilisé quand il n’y a pas de données à manipuler.
    Par exemple, le widget des médias interagit directement avec l’API des médias.
    """

    def get_wire_type(self):
        return Never


class ValueStore(BaseStore):
    """
    Cet adapter est utilisé pour vérifier qu’une valeur appartient à une liste.
    """

    class ConfigSchema(BaseStore.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    # TODO: default widget

    def get_wire_type(self):
        return Literal[tuple(value["value"] for value in self.config["values"])]


class ListStore(BaseStore):
    """
    Idem que ValueStore, mais pour une liste de données.
    """

    class ConfigSchema(BaseStore.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    # TODO: default widget

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self.config["values"])]]


class StringStore(BaseStore):
    def _get_default_widget(self, data, **kwargs):
        from ..widgets import TextWidget

        return TextWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class BooleanStore(BaseStore):
    def _get_default_widget(self, data, **kwargs):
        from ..widgets import CheckboxWidget

        return CheckboxWidget(data, **kwargs)

    def get_wire_type(self):
        return bool


class IntegerStore(BaseStore):
    key = "integer"

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import NumberWidget

        return NumberWidget({"step": 1}, **kwargs)

    def get_wire_type(self):
        return int


class FloatStore(BaseStore):
    def _get_default_widget(self, data, **kwargs):
        from ..widgets import NumberWidget

        return NumberWidget(data, **kwargs)

    def get_wire_type(self):
        return float


class DateStore(BaseStore):
    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DateWidget

        return DateWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class TimeStore(BaseStore):
    def _get_default_widget(self, data, **kwargs):
        from ..widgets import TimeWidget

        return TimeWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class UUIDStore(BaseStore):
    key = "uuid"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("uuid"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import TextWidget

        return TextWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class UserStore(BaseStore):
    key = "user"

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

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("observer_list"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatalistWidget

        # TODO: instancier DatalistWidget avec les bon paramètres
        raise NotImplementedError("Missing default widget for adapter 'observer_list'")

    def get_wire_type(self):
        return list[int]


class TaxonomyStore(BaseStore):
    key = "taxonomy"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("taxonomy"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import TaxonomyWidget

        return TaxonomyWidget(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyListStore(BaseStore):
    key = "taxonomy_list"

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

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("dataset"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import DatasetWidget

        return DatasetWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        return int


class HabitatStore(BaseStore):
    key = "habitat"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.Equal("habitat"))

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import HabitatWidget

        return HabitatWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        return int


class AreasStore(BaseStore):
    key = "areas"

    class ConfigSchema(BaseStore.ConfigSchema):
        type = fields.Str(validate=validate.OneOf(["area", "areas"]))
        many = fields.Boolean(load_default=True)

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import AreasWidget

        return AreasWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        if self.config.many:
            return list[int]
        else:
            return int


class TypesSiteStore(BaseStore):
    key = "types_site"

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


# TODO: date, site, sites_group, area
# TODO: observer_list, taxonomy_list, municipality? accepté par la route util/<type_util>/
