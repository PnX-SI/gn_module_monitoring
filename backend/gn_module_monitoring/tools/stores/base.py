from collections import UserDict
from typing import Any, Literal, Never

import marshmallow as ma
from marshmallow import fields, pre_load, validate
from sqlalchemy.orm import ColumnProperty, RelationshipProperty

from gn_module_monitoring.tools.utils import ValueLabelField, schema_context

STORE_MAP: dict[str, type] = {}


class BaseStore(UserDict):
    class ConfigSchema(ma.Schema):
        """
        Schéma de configuration du store.
        """

        class Meta:
            unknown = ma.RAISE

        type = fields.Str(required=True)
        required = fields.Boolean(load_default=False)

        @pre_load
        def load_default_type(self, data, **kwargs):
            if "type" not in data:
                data["type"] = schema_context.get()["store"].key
            return data

    class Field(fields.Field):
        """
        Champ marshmallow d’un store : conversion et validation entre l’API et le stockage.
        """

        def __init__(self, store, **kwargs):
            super().__init__(
                required=store["required"], allow_none=not store["required"], **kwargs
            )
            self.store = store

        def _deserialize(self, value, attr, data, **kwargs):
            """
            Fonction de validation des données reçu par l’API.
            En cas d’erreur(s), lever une exception ValidationError.
            Retourne la valeur qui doit être stocké en base.
            """
            raise NotImplementedError

        def _serialize(self, value, attr, obj, **kwargs):
            """
            Fonction de déserialisation des données depuis la base avant l’envoi à l’API.
            Sauf cas particulier, la données peut être envoyé telle quelle à l’API.
            """
            return value

        @property
        def wire_type(self):
            raise NotImplementedError

    def __init_subclass__(cls, **kwargs):
        # Enregistrement automatique dans STORE_MAP
        super().__init_subclass__(**kwargs)
        if "key" in cls.__dict__:
            STORE_MAP[cls.key] = cls

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
        self.config_schema = self.ConfigSchema()
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
                from gn_module_monitoring.tools.stores.type import BaseTypeStore

                for subcls in BaseTypeStore.__subclasses__():
                    if subcls.is_suitable_for_column(column):
                        return subcls
        raise ValueError(f"Unable to find proper store for column '{attr.key}'")

    def to_field(self):
        return self.Field(self)

    def get_wire_type(self) -> type:
        return self.to_field().wire_type

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

    class Field(BaseStore.Field):
        wire_type = Never


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

    class Field(BaseStore.Field):
        @property
        def wire_type(self):
            return Literal[tuple(item["value"] for item in self.store["values"])]

        def _deserialize(self, value, attr, data, **kwargs):
            allowed = [item["value"] for item in self.store["values"]]
            return fields.Raw(validate=validate.OneOf(allowed)).deserialize(value)


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

    class Field(BaseStore.Field):
        @property
        def wire_type(self):
            return list[Literal[tuple(item["value"] for item in self.store["values"])]]

        def _deserialize(self, value, attr, data, **kwargs):
            allowed = [item["value"] for item in self.store["values"]]
            return fields.List(fields.Raw(validate=validate.OneOf(allowed))).deserialize(value)


# TODO: date, site, sites_group, area
# TODO: observer_list, taxonomy_list, municipality? accepté par la route util/<type_util>/

