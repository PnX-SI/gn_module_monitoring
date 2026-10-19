import logging
from collections import UserDict
from typing import Literal, Never, Any

import sqlalchemy as sa
import marshmallow as ma
from flask import current_app
from sqlalchemy.orm import ColumnProperty, RelationshipProperty
from marshmallow import fields, pre_load, ValidationError

from gn_module_monitoring import MODULE_CODE
from ..utils import ValueLabelField, schema_context

log = logging.getLogger(__name__)

STORE_MAP: dict[str, type] = {}


class BaseStore(UserDict):
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        type = fields.Str(required=True)

        @pre_load
        def load_default_type(self, data, **kwargs):
            if "type" not in data:
                data["type"] = schema_context.get()["store"].key
            return data

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "key" in cls.__dict__:
            STORE_MAP[cls.key] = cls

    @property
    def config_schema_class(self):
        return self.ConfigSchema

    @classmethod
    def get_store_from_attr(cls, attr):
        """
        Retourne la classe de store adaptée à un attribut de mapper (`mapper.attrs[field_name]`) :
        - RelationshipProperty -> store M2M adapté
        - ColumnProperty avec FK -> store FK adapté
        - ColumnProperty sans FK -> store de type adapté
        """
        if isinstance(attr, RelationshipProperty):
            from gn_module_monitoring.tools.stores.relationships.m2m import BaseManyToManyStore

            for subcls in BaseManyToManyStore.__subclasses__():
                if subcls.is_suitable_for_relationship(attr):
                    return subcls
            raise ValueError(f"Unable to find proper store for relationship '{attr.key}'")
        elif isinstance(attr, ColumnProperty) and len(attr.columns) == 1:
            column = attr.columns[0]
            if column.foreign_keys:
                from gn_module_monitoring.tools.stores.relationships.m2o import BaseForeignKeyStore

                for subcls in BaseForeignKeyStore.__subclasses__():
                    if subcls.is_suitable_for_column(column):
                        return subcls
            else:
                for subcls in BaseTypeStore.__subclasses__():
                    if subcls.is_suitable_for_column(column):
                        return subcls
        raise ValueError(f"Unable to find proper store for column '{attr.key}'")

    def __init__(self, data=None, **kwargs):
        super().__init__()
        data = data or {}
        if "type_util" in data:
            self.extra_data = data
            # retro-compat.
            kwargs["unknown"] = ma.EXCLUDE
        else:
            self.extra_data = None
        ctx = schema_context.get()
        self.entity = ctx["entity"]
        self.field_name = ctx["field_name"]
        self.native_attr = self.entity.get_model_attrs().get(self.field_name)
        self.config_schema = self.config_schema_class()
        with schema_context(store=self):
            self.data = self.config_schema.load(data, **kwargs)

    def dump_config(self):
        return self.config_schema.dump(self.data)

    def get_default_widget(self, data=None, **kwargs):
        # Gestion de la rétro-compat: si l’adapter a été initialisé en mode retro-compat.,
        # on initialise le widget en mode retro-compat.
        data = data or {}
        if self.extra_data:
            return self._get_default_widget(
                {**{k: v for k, v in self.extra_data.items() if k != "type"}, **data},
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

    key = "dummy"

    def get_wire_type(self):
        return Never


class ValueStore(BaseStore):
    """
    Cet adapter est utilisé pour vérifier qu’une valeur appartient à une liste.
    """

    key = "value"

    class ConfigSchema(BaseStore.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import SelectWidget

        return SelectWidget({"values": self["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return Literal[tuple(value["value"] for value in self["values"])]


class ListStore(BaseStore):
    """
    Idem que ValueStore, mais pour une liste de données.
    """

    key = "list"

    class ConfigSchema(BaseStore.ConfigSchema):
        values = fields.List(ValueLabelField(), required=True)

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import CheckboxWidget

        return CheckboxWidget({"values": self["values"], **(data or {})}, **kwargs)

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self["values"])]]


class BaseTypeStore(BaseStore):
    """
    Store pour une colonne simple dont le type SQL correspond à `sql_type`.
    """

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

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TextWidget

        return TextWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class BooleanStore(BaseTypeStore):
    key = "bool"
    sql_type = sa.types.Boolean

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import BoolCheckboxWidget

        return BoolCheckboxWidget(data, **kwargs)

    def get_wire_type(self):
        return bool


class IntegerStore(BaseTypeStore):
    key = "integer"
    sql_type = sa.types.Integer

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NumberWidget

        return NumberWidget({"step": 1}, **kwargs)

    def get_wire_type(self):
        return int


class FloatStore(BaseTypeStore):
    key = "float"
    sql_type = sa.types.Float

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NumberWidget

        return NumberWidget(data, **kwargs)

    def get_wire_type(self):
        return float


class DateStore(BaseTypeStore):
    key = "date"
    sql_type = sa.types.Date

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DateWidget

        return DateWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class DateTimeStore(BaseTypeStore):
    key = "datetime"
    sql_type = sa.types.DateTime

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TimeWidget

        return TimeWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class UUIDStore(BaseTypeStore):
    key = "uuid"
    sql_type = sa.types.Uuid

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TextWidget

        return TextWidget(data, **kwargs)

    def get_wire_type(self):
        return str


# TODO: date, site, sites_group, area
# TODO: observer_list, taxonomy_list, municipality? accepté par la route util/<type_util>/
