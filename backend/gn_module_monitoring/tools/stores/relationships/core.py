import logging
from functools import cache

import sqlalchemy as sa
from marshmallow import fields, validates, validates_schema, ValidationError
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import RelationshipProperty

from geonature.utils.env import db

from gn_module_monitoring.tools.utils import schema_context

from ..base import BaseStore

log = logging.getLogger(__name__)


class BaseRelationshipStore(BaseStore):
    """
    Base commune des stores qui pointent vers un modèle cible :
    many-to-one (FK) et many-to-many (relationship via table d'association).
    """

    # Modèle métier ciblé par le store (dump only), ex. "user" pour UserStore et UsersStore
    # C’est cette propriété qui est dumpée dans type_util.
    model = None

    class ConfigSchema(BaseStore.ConfigSchema):
        """Paramètres communs : colonnes de stockage de la cible."""

        model = fields.Str(dump_only=True)

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
                log.warning(
                    f"{self.entity} - {self.field_name} - "
                    "You have set 'storage_col' and 'storage_cols'. "
                    "You should take a time to fix your data and remove 'storage_col'."
                )

    class Field(fields.Field):
        """
        Champ marshmallow d’une relation : la valeur échangée avec l’API est une clé primaire
        (ou une liste de clés primaires).
        """

        def __init__(self, store, **kwargs):
            super().__init__(**store._get_field_kwargs(), **kwargs)
            self.store = store

        def get_value(self, obj, attr, accessor=None, default=None):
            """
            Les champs non natifs stockent la PK, et pour éviter de fetcher l’objet, `_serialize`
            attend uniquement la PK. Pour les champs natifs, on a l’objet, dont on récupère donc
            la (les) PK, comme attendue par `_serialize`.
            """
            value = super().get_value(obj, attr, accessor, default)
            native_attr = self.store.native_attr
            if value is None or not isinstance(native_attr, RelationshipProperty):
                return value
            pk = self.store.get_model_pk().name
            if native_attr.uselist:
                return [getattr(instance, pk) for instance in value]
            else:
                return getattr(value, pk)

        def _deserialize(self, value, attr, data, **kwargs):
            """
            Reçoit la (m2o) ou les (m2m) PK par l’API, et renvoi la ou les instance(s) associée(s).
            Le chargement des instances est nécessaire à d’éventuels contrôles, au contexte CEL,
            et éventuellement à to_storage lorsque l’on souhaite stocker divers colonne de notre objet.
            """
            raise NotImplementedError

        def _serialize(self, value, attr, obj, **kwargs):
            """
            Reçoit la (m2o) ou les (m2m) PK depuis la base (directement ou après appelle à from_storage
            pour les champs non natifs), et renvoi la ou les PK telle(s) quelle(s), d’où l’implémentation
            par défaut renvoyant simplement value.
            """
            return value

    def _to_storage(self, instance):
        # traite un unique élément, appelé telle quelle par M2O, sur chaque item par M2M
        if self.get("storage_cols"):
            # we store a dict with given columns
            return {col: getattr(instance, col) for col in self["storage_cols"]}
        elif self.get("storage_col"):
            # we store this column
            return getattr(instance, self["storage_col"])
        else:
            # we store the pk
            return getattr(instance, self.get_model_pk().name)

    def _from_storage(self, value):
        # traite un unique élément, appelé telle quelle par M2O, sur chaque item par M2M
        pk = self.get_model_pk()
        if isinstance(value, dict):
            # La donnée stockée est un dict, qu’on peut supposer contenir la clé primaire
            # (forcé par validate_storage_cols)
            return value[pk.name]
        elif storage_col := self.get("storage_col"):
            # La donnée stockée est la colonne 'storage_col'
            # On vérifie tous de même le type dès fois que la configuration soit incorrecte.
            python_type = self.get_model_mapper().attrs[storage_col].columns[0].type.python_type
            if not isinstance(value, python_type):
                raise ValueError(
                    f"Unexpected value '{value}' : mauvais type, attendu : '{python_type}'"
                )
            try:
                return db.session.execute(
                    sa.select(pk).where(
                        getattr(self.get_model(), storage_col) == value,
                        *self._get_storage_filters(),
                    )
                ).scalar_one()
            except NoResultFound:
                raise ValueError(f"Unexpected value '{value}' : aucune instance trouvée.")
            except MultipleResultsFound:
                raise ValueError(f"Unexpected value '{value}' : plusieurs instances trouvées.")
        else:
            # Donnée stockée sous forme de clé primaire en théorie
            return value

    def _get_storage_filters(self):
        # Conditions supplémentaires pour retrouver une instance à partir de storage_col
        return []

    def get_field(self) -> fields.Field:
        return self.Field(self)

    def dump_config(self):
        return self.config_schema.dump({**self.data, "model": self.model})

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
