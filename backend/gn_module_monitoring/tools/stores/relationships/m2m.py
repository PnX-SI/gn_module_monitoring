import logging

from marshmallow import fields, validate, ValidationError
from flask import current_app
from sqlalchemy.orm import RelationshipProperty

from geonature.utils.env import db

from gn_module_monitoring import MODULE_CODE

from .core import BaseRelationshipStore
from .m2o import NomenclatureStore

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


class AreasStore(BaseManyToManyStore):
    key = "areas"

    @classmethod
    def get_model(cls):
        from ref_geo.models import LAreas

        return LAreas

    class ConfigSchema(BaseManyToManyStore.ConfigSchema):
        area_code = fields.Str()

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import AreasWidget

        return AreasWidget({**(data or {}), "multiple": True}, **kwargs)


class DatasetsStore(BaseManyToManyStore):
    key = "datasets"

    @classmethod
    def get_model(cls):
        from geonature.core.gn_meta.models import TDatasets

        return TDatasets

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatasetWidget

        return DatasetWidget({**(data or {}), "multi_select": True}, **kwargs)


class NomenclaturesStore(BaseManyToManyStore):
    key = "nomenclatures"

    @classmethod
    def get_model(cls):
        from pypnnomenclature.models import TNomenclatures

        return TNomenclatures

    class ConfigSchema(NomenclatureStore.ConfigSchema, BaseManyToManyStore.ConfigSchema):
        pass

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NomenclatureWidget

        return NomenclatureWidget({**(data or {}), "multi_select": True}, **kwargs)


class ModulesStore(BaseManyToManyStore):
    key = "modules"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringModules

        return TMonitoringModules

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import ModuleWidget

        return ModuleWidget(
            {"attribut_label": "Modules", **(data or {}), "multiple": True}, **kwargs
        )


class UsersStore(BaseManyToManyStore):
    key = "users"

    @classmethod
    def get_model(cls):
        from pypnusershub.db.models import User

        return User

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import ObserversWidget

        return ObserversWidget(data, **kwargs)
