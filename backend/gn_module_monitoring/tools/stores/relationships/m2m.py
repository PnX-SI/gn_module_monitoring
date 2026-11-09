import logging

from marshmallow import fields, validate, ValidationError
from flask import current_app
from sqlalchemy.orm import RelationshipProperty

from geonature.utils.env import db

from gn_module_monitoring import MODULE_CODE

from .core import BaseRelationshipStore
from .mixin import AreaMixin, DatasetMixin, ModuleMixin, NomenclatureMixin, UserMixin
from .utils import validate_areas_of_type, validate_observers_in_list

log = logging.getLogger(__name__)


class BaseManyToManyStore(BaseRelationshipStore):
    """
    Store pour une relation many-to-many : le champ est une relationship SQLAlchemy
    passant par une table d'association (paramètre `secondary`), et non une colonne.

    Pas de to_storage / from_storage : la relation est native, elle n’est pas stockée dans `data`.
    Asymétrie entre les deux sens :
    - chargement (API → DB) : `Field._deserialize` renvoie une liste d’instances, pour la validation ;
    - dump (DB → API) : la valeur lue est la relation elle-même, donc une liste d’instances,
      et `Field._serialize` en extrait les clés primaires.
    """

    class Field(BaseRelationshipStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            """
            La valeur reçue de l’API est une liste de clés primaires de la cible.
            Vérifie l’existence de chaque ligne, puis renvoie les objets.
            """
            if value is None:
                return None
            store = self.store
            model = store.get_model()
            pk = store.get_model_pk()
            ids = fields.List(fields.Integer(strict=True)).deserialize(value)
            instances = []
            for id in ids:
                instance = db.session.get(model, id)
                if instance is None:
                    raise ValidationError(
                        f"Aucune instance de {model.__name__} pour {pk.name} = '{id}'."
                    )
                instances.append(instance)
            return instances

    @classmethod
    def is_suitable_for_relationship(cls, relationship):
        return relationship.secondary is not None and relationship.mapper.class_ is cls.get_model()

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        if self.native_attr is not None:
            # Cas attendu : une relationship passant par une table d'association, vers self.get_model()
            if not (
                isinstance(self.native_attr, RelationshipProperty)
                and self.is_suitable_for_relationship(self.native_attr)
            ):
                error_message = (
                    f"Le store {self.key} n'est pas adapté à l'attribut {self.field_name} : "
                    f"il doit être une relation many-to-many vers {self.get_model().__name__}."
                )
                if current_app.config[MODULE_CODE]["STRICT"]:
                    raise ValidationError({self.field_name: error_message})
                else:
                    log.warning(f"Validation warning: {error_message}")

    def get_api_type(self) -> type:
        return list[int]

    def get_python_type(self) -> type:
        return list[self.get_model()]


class TypesSiteStore(BaseManyToManyStore):
    key = "types_site"
    model = "types_site"

    @classmethod
    def get_model(cls):
        from geonature.core.gn_monitoring.models import BibTypeSite

        return BibTypeSite

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

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


class AreasStore(AreaMixin, BaseManyToManyStore):
    key = "areas"

    class Field(BaseManyToManyStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            instances = super()._deserialize(value, attr, data, **kwargs)
            if instances and self.store.area_type:
                validate_areas_of_type(instances, self.store.area_type)
            return instances

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import AreasWidget

        return AreasWidget({**(data or {}), "multiple": True}, **kwargs)


class DatasetsStore(DatasetMixin, BaseManyToManyStore):
    key = "datasets"

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatasetWidget

        return DatasetWidget({**(data or {}), "multi_select": True}, **kwargs)


class NomenclaturesStore(NomenclatureMixin, BaseManyToManyStore):
    key = "nomenclatures"

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NomenclatureWidget

        return NomenclatureWidget({**(data or {}), "multi_select": True}, **kwargs)


class ModulesStore(ModuleMixin, BaseManyToManyStore):
    key = "modules"

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import ModuleWidget

        return ModuleWidget(
            {"attribut_label": "Modules", **(data or {}), "multiple": True}, **kwargs
        )


class UsersStore(UserMixin, BaseManyToManyStore):
    key = "users"

    class Field(BaseManyToManyStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            instances = super()._deserialize(value, attr, data, **kwargs)
            if instances and self.store.list:
                validate_observers_in_list(instances, self.store.list)
            return instances

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import ObserversWidget

        return ObserversWidget(data, **kwargs)
