import logging

import sqlalchemy as sa
from sqlalchemy import ARRAY
from marshmallow import fields, validate, ValidationError
from flask import current_app
from sqlalchemy.orm import RelationshipProperty

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.tools.cel import object_to_cel

from .cache import get_instance
from .core import BaseRelationshipStore
from .mixin import AreaMixin, DatasetMixin, ModuleMixin, NomenclatureMixin, UserMixin
from .utils import validate_areas_of_type, validate_observers_in_list

log = logging.getLogger(__name__)


class BaseManyToManyStore(BaseRelationshipStore):
    """
    Store pour une relation many-to-many : le champ est une relationship SQLAlchemy
    passant par une table d'association (paramètre `secondary`), et non une colonne.

    Champ natif (relation SQLAlchemy) : pas de stockage, la relation est lue et écrite directement.
    Champ non natif (stocké dans `data`) : chaque élément est converti comme pour un store M2O
    (clé primaire, `storage_col` ou `storage_cols`), et la liste entière est stockée.
    Asymétrie entre les deux sens :
    - chargement (API → DB) : `Field._deserialize` renvoie une liste d’instances, pour la validation ;
      `to_json_storage` la convertit en liste de valeurs stockables ;
    - dump (DB → API) : `from_json_storage` renvoie une liste de clés primaires, et `Field._serialize`
      la renvoie telle quelle. Pour un champ natif, `Field.get_value` extrait les clés primaires
      de la relation (liste d’instances).
    """

    # Le store stocke une liste de clés primaires de la cible (entiers)
    sql_type = ARRAY(sa.types.Integer)

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
                instance = get_instance(model, id)
                if instance is None:
                    raise ValidationError(
                        f"Aucune instance de {model.__name__} pour {pk.name} = '{id}'."
                    )
                instances.append(instance)
            return instances

    @classmethod
    def is_suitable_for_relationship(cls, relationship):
        return relationship.secondary is not None and relationship.mapper.class_ is cls.get_model()

    def to_cel(self, value):
        """Relation many-to-many : `value` est la liste des objets chargés (ou None), chacun en objet CEL."""
        if value is None:
            return None
        return [object_to_cel(instance) for instance in value]

    def to_json_storage(self, value):
        if value is None:
            return None
        return [self._to_storage(instance) for instance in value]

    def from_json_storage(self, value):
        if value is None:
            return None
        return [self._from_storage(item) for item in value]

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        if current_app.config[MODULE_CODE]["STRICT"] and self.native_attr is not None:
            # Cas attendu : une relationship passant par une table d'association, vers self.get_model()
            if not (
                isinstance(self.native_attr, RelationshipProperty)
                and self.is_suitable_for_relationship(self.native_attr)
            ):
                error_message = (
                    f"Le store {self.key} n'est pas adapté à l'attribut {self.field_name} : "
                    f"il doit être une relation many-to-many vers {self.get_model().__name__}."
                )
                raise ValidationError({self.field_name: error_message})

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
                **(data or {}),
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

        return DatasetWidget({**(data or {}), "multiple": True}, **kwargs)


class NomenclaturesStore(NomenclatureMixin, BaseManyToManyStore):
    key = "nomenclatures"

    class Field(BaseManyToManyStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            instances = super()._deserialize(value, attr, data, **kwargs)
            if instances:
                self.store.validate_nomenclatures_of_type(instances)
            return instances

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NomenclatureWidget

        return NomenclatureWidget({**(data or {}), "multiple": True}, **kwargs)


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
