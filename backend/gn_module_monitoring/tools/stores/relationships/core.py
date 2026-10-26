import logging
from functools import cache

import sqlalchemy as sa
from marshmallow import fields, validates, validates_schema, ValidationError

from gn_module_monitoring.tools.utils import schema_context

from ..base import BaseStore

log = logging.getLogger(__name__)


class BaseRelationshipStore(BaseStore):
    """
    Base commune des stores qui pointent vers un modèle cible :
    many-to-one (FK) et many-to-many (relationship via table d'association).
    """

    class ConfigSchema(BaseStore.ConfigSchema):
        """Paramètres communs : colonnes de stockage de la cible."""

        # Stock cette propriété du modèle associé au store.
        storage_col = fields.Str()
        # Stock un object contenant cette liste de propriétés du modèle.
        storage_cols = fields.List(fields.Str())

        @validates("storage_col")
        def validate_storage_col(self, value, **kwargs):
            store = schema_context.get()["store"]
            if value not in store.get_model_mapper().column_attrs:
                raise ValidationError(
                    f"La colonne '{value}' n'existe pas dans le modèle {store.get_model().__name__}."
                )

        @validates("storage_cols")
        def validate_storage_cols(self, values, **kwargs):
            store = schema_context.get()["store"]
            columns = store.get_model_mapper().column_attrs
            invalid = [value for value in values if value not in columns]
            if invalid:
                raise ValidationError(
                    f"Les colonnes {invalid} n'existent pas dans le modèle {store.get_model().__name__}."
                )
            pk_name = store.get_model_pk().name
            if pk_name not in values:
                raise ValidationError(
                    f"'storage_cols' **doit** contenir la PK du model ({pk_name})."
                )

        @validates_schema
        def validate_mutually_exclusive(self, data, **kwargs):
            if data.get("storage_col") is not None and data.get("storage_cols") is not None:
                # L’intérêt d’utiliser les deux est de pouvoir sauvegarder plusieurs propriétés,
                # mais si les données contiennent encore une colonne simple, on se base sur
                # storage_col pour savoir de quoi il s’agit.
                log.warnings(
                    f"{self.entity} - {self.field_name} - "
                    "You have set 'storage_col' and 'storage_cols'. "
                    "You should take a time to fix your data and remove 'storage_col'."
                )

    @classmethod
    def get_model(cls):
        """
        Retourne le modèle cible pour l’implémentation concrète du store.
        """
        raise NotImplementedError

    @classmethod
    def get_model_mapper(cls):
        return sa.inspect(cls.get_model())

    @classmethod
    @cache
    def get_model_pk(cls):
        """
        Retourne la colonne clé primaire du modèle cible de ce store.
        Lève une erreur si le modèle n'a pas de clé primaire simple.
        """
        pk = cls.get_model_mapper().primary_key
        if len(pk) != 1:
            raise ValueError(
                f"{cls.get_model().__name__} doit avoir une clé primaire simple. Trouvé : {pk}."
            )
        return pk[0]
