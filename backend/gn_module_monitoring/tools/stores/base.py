from collections import UserDict
from typing import Any, Literal, Never

import marshmallow as ma
from marshmallow import fields, pre_load, validate
from sqlalchemy.orm import ColumnProperty, RelationshipProperty

from gn_module_monitoring.tools.utils import (
    ValueLabelField,
    schema_context,
)

STORE_MAP: dict[str, type] = {}


class BaseStore(UserDict):
    class ConfigSchema(ma.Schema):
        """
        Schéma de configuration du store.
        """

        class Meta:
            unknown = ma.RAISE

        type = fields.Str(required=True)

        # required, required_cel & validate_cel are defined at field level

        @pre_load
        def load_default_type(self, data, **kwargs):
            if "type" not in data:
                data["type"] = schema_context.get()["store"].key
            return data

    def __init_subclass__(cls, **kwargs):
        # Enregistrement automatique dans STORE_MAP
        super().__init_subclass__(**kwargs)
        if "key" in cls.__dict__:
            STORE_MAP[cls.key] = cls

    def __init__(
        self, data=None, *, required=False, required_cel=None, validate_cel=None, **kwargs
    ):
        super().__init__()
        self.required = required
        self.required_cel = required_cel
        self.validate_cel = validate_cel
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

    def get_field(self) -> fields.Field:
        """
        Champ marshmallow du store : valide et convertit la valeur reçue de l’API en valeur Python,
        et convertit la valeur Python en valeur envoyée à l’API.
        """
        raise NotImplementedError

    def get_api_type(self) -> type:
        """Type Python de la valeur échangée avec l’API."""
        raise NotImplementedError

    def get_python_type(self) -> type:
        """Type Python de la valeur renvoyée par le champ après le chargement d’un objet."""
        raise NotImplementedError

    def _get_field_kwargs(self) -> dict:
        """Options communes des champs marshmallow du store."""
        return {"required": self.required, "allow_none": not self.required}

    def to_storage(self, value):
        """
        Convertit une valeur Python en valeur stockable dans la colonne JSON `data`
        (uniquement pour les champs non natifs). Par défaut, la valeur est inchangée.
        """
        return value

    def from_storage(self, value):
        """
        Convertit une valeur lue depuis la colonne JSON `data` en valeur Python
        (inverse de `to_storage`). Par défaut, la valeur est inchangée.
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

    def get_api_type(self) -> type:
        return Never

    def get_python_type(self) -> type:
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

    def get_field(self) -> fields.Field:
        allowed = [item["value"] for item in self["values"]]
        return fields.Raw(validate=validate.OneOf(allowed), **self._get_field_kwargs())

    def get_api_type(self) -> type:
        return Literal[tuple(item["value"] for item in self["values"])]

    def get_python_type(self) -> type:
        return self.get_api_type()


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

    def get_field(self) -> fields.Field:
        allowed = [item["value"] for item in self["values"]]
        return fields.List(
            fields.Raw(validate=validate.OneOf(allowed)), **self._get_field_kwargs()
        )

    def get_api_type(self) -> type:
        return list[Literal[tuple(item["value"] for item in self["values"])]]

    def get_python_type(self) -> type:
        return self.get_api_type()


# TODO: date, site, sites_group, area
# TODO: observer_list, taxonomy_list, municipality? accepté par la route util/<type_util>/
