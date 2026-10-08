from functools import cache, cached_property
from typing import Literal, Never, Any

import sqlalchemy as sa
import marshmallow as ma
from marshmallow import (
    fields,
    validate,
    pre_load,
    post_load,
    validates,
    validates_schema,
    ValidationError,
)

from geonature.utils.env import db

from gn_module_monitoring.command.check.utils import ValueLabelField


class BaseAdapter:
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

    @classmethod
    def get_config_schema_class(cls):
        return cls.ConfigSchema

    def __init__(self, data=None, **kwargs):
        self.config = self.get_config_schema_class()().load(data or {}, **kwargs)

    def get_default_widget(self, data, **kwargs):
        """
        Widget par défaut pour cet adapteur. Si l’utilisateur ne définie pas de widget dans la config,
        alors ce widget sera utilisé.
        """
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


class DummyAdapter(BaseAdapter):
    """
    Cet apapter est utilisé quand il n’y a pas de données à manipuler.
    Par exemple, le widget des médias interagit directement avec l’API des médias.
    """

    def get_wire_type(self):
        return Never


class ValueAdapter(BaseAdapter):
    """
    Cet adapter est utilisé pour vérifier qu’une valeur appartient à une liste.
    """

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        values = fields.List(ValueLabelField(), required=True)

    # TODO: default widget

    def get_wire_type(self):
        return Literal[tuple(value["value"] for value in self.config["values"])]


class ListAdapter(BaseAdapter):
    """
    Idem que ValueAdapter, mais pour une liste de données.
    """

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        values = fields.List(ValueLabelField(), required=True)

    # TODO: default widget

    def get_wire_type(self):
        return list[Literal[tuple(value["value"] for value in self.config["values"])]]


class StringAdapter(BaseAdapter):
    def get_default_widget(self, data, **kwargs):
        from .widgets import TextWidget

        return TextWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class BooleanAdapter(BaseAdapter):
    def get_default_widget(self, data, **kwargs):
        from .widgets import CheckboxWidget

        return CheckboxWidget(data, **kwargs)

    def get_wire_type(self):
        return bool


class IntAdapter(BaseAdapter):
    def get_default_widget(self, data, **kwargs):
        # TODO: créer un widget integer
        raise NotImplementedError

    def get_wire_type(self):
        return int


class FloatAdapter(BaseAdapter):
    def get_default_widget(self, data, **kwargs):
        from .widgets import NumberWidget

        return NumberWidget(data, **kwargs)

    def get_wire_type(self):
        return float


class DateAdapter(BaseAdapter):
    def get_default_widget(self, data, **kwargs):
        from .widgets import DateWidget

        return DateWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class TimeAdapter(BaseAdapter):
    def get_default_widget(self, data, **kwargs):
        from .widgets import TimeWidget

        return TimeWidget(data, **kwargs)

    def get_wire_type(self):
        return str


class UserAdapter(BaseAdapter):
    key = "user"

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        type = fields.Str(validate=validate.Equal("user"))

    def get_default_widget(self, data, **kwargs):
        from .widgets import DatalistWidget

        # TODO: instancier DatalistWidget avec les bon paramètres
        raise NotImplementedError("Missing default widget for adapter 'user'")

    def get_wire_type(self):
        return int


class NomenclatureAdapter(BaseAdapter):
    key = "nomenclature"

    @cache
    @staticmethod
    def get_nomenclature_columns():
        from pypnnomenclature.models import TNomenclatures

        return sa.inspect(TNomenclatures).columns

    @classmethod
    def get_config_schema_class(cls):
        from pypnnomenclature.models import BibNomenclaturesTypes

        types_mnemoniques = list(
            db.session.execute(sa.select(BibNomenclaturesTypes.mnemonique)).scalars()
        )
        columns = NomenclatureAdapter.get_nomenclature_columns()

        class ConfigSchema(ma.Schema):
            class Meta:
                unknown = ma.RAISE

            type = fields.Str(validate=validate.Equal("nomenclature"))
            nomenclature_type = fields.Str(
                validate=validate.OneOf(types_mnemoniques),
                required=True,  # TODO: à confirmer
            )
            cd_nomenclatures = fields.List(fields.Str())
            # Stock cette propriété des nomenclatures
            storage_col = fields.Str(validate=validate.OneOf(columns.values()))
            # Stock un object contenant cette liste de propriétés des nomenclatures
            storage_cols = fields.List(fields.Str(validate=validate.OneOf(columns.values())))

            @validates("storage_cols")
            def ensure_id_nomenclature(self, value):
                if "id_nomenclature" not in value:
                    raise ValidationError(
                        "Le champs 'id_nomenclature' **doit** faire partie des colonnes enregistrées."
                    )

            @pre_load
            def retrocompat(self, data, **kwargs):
                if "code_nomenclature_type" in data:
                    data["nomenclature_type"] = data.pop("code_nomenclature_type")
                return data

            @validates_schema
            def validate_cd_nomenclatures(self, data, **kwargs):
                # TODO: vérifier que les cd_nomenclature fournit dans la liste existe bien
                # pour le type de nomenclature demandé.
                pass

            @validates_schema
            def set_defaults(self, data, **kwargs):
                # Par défaut, on stock ces 3 colonnes de la nomenclature
                if "storage_col" not in data and "storage_cols" not in data:
                    data["storage_cols"] = ["id_nomenclature", "cd_nomenclature", "label_default"]

            @validates_schema
            def validate_mutually_exclusive(self, data, **kwargs):
                if data.get("storage_col") is not None and data.get("storage_cols") is not None:
                    raise ValidationError(
                        "Only one of 'storage_col' or 'storage_cols' may be provided."
                    )

            @post_load
            def load_nomenclature_type(self, data, **kwargs):
                from .nomenclature import get_nomenclature_type

                if "nomenclature_type" in data:
                    # should not fail thanks to field validator
                    data["nomenclature_type"] = get_nomenclature_type(data["nomenclature_type"])
                return data

        return ConfigSchema

    def get_default_widget(self, data, **kwargs):
        from .widgets import NomenclatureWidget

        return NomenclatureWidget(data, **kwargs)

    def get_wire_type(self):
        return int

    @cached_property
    def storage_type(self):
        columns = NomenclatureAdapter.get_nomenclature_columns()
        if self.config.storage_col:
            return columns[self.config.storage_col].type.python_type
        else:
            return list[(columns[col].type.python_type for col in self.config.storage_cols)]

    @cached_property
    def str_column(self):
        """
        Cette fonction analyse storage_cols, et détermine si une et une seule propriété
        indique un champs texte. Par exemple, si storage_cols=["id_nomenclature","cd_nomenclature"].
        Dans ce cas, on pourra rechercher une nomenclature en se basant sur cette propriété.
        """
        columns = NomenclatureAdapter.get_nomenclature_columns()
        if self.config.storage_col:  # par principe, on couvre ce cas aussi
            columns = {self.config.storage_col: columns[self.config.storage_col]}
        else:
            columns = {col_name: columns[col_name] for col_name in self.config.storage_cols}
        str_columns = [
            col_name for col_name, col in columns.items() if col.type.python_type == str
        ]
        if len(str_columns) == 1:
            self.str_column = str_columns[0]
        else:
            self.str_column = None

    def storage_to_wire(self, value: Any) -> Any:
        # Cas idéaux
        if self.storage_cols and isinstance(value, dict):
            return value["id_nomenclature"]
        elif self.storage_col and isinstance(value, self.storage_type):
            return value
        # Maintenant, les rétro-compat…
        elif isinstance(value, int):
            # Bon, on est pas censé avoir stocké l’id_nomenclature mais on va supposer que c’est de ça qu’il s’agit
            return value
        elif isinstance(value, str) and self.str_column:
            # Si on trouve une nomenclature qui correspond en se basant sur str_column, on l’utilise
            from .nomenclature import get_nomenclature

            nomenclature = get_nomenclature(
                type=self.config["nomenclature_type"], *{self.str_column: value}
            )
            if nomenclature is not None:
                return nomenclature
        # Pas de solution trouvé
        return ValueError(
            f"Unexpected value '{value}'"
        )  # FIXME: créer une exception dédié aux problèmes de décodage

    def check_stored_value(self, entity, row_id, field_name, value, fix):
        # TODO: cette fonction s’attend uniquement à trouver un id_nomenclature
        # Il faut la faire évoluer pour gérer storage_col & storage_cols
        import click

        from pypnnomenclature.models import TNomenclatures

        from .nomenclature import get_nomenclature

        updated_value = value

        nomenclature_type = self.config["nomenclature_type"]

        if type(value) != int:
            yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - valeur '{value}' : pas un entier"
            if type(value) == str:
                nomenclature = get_nomenclature(
                    nomenclature_type, TNomenclatures.cd_nomenclature.ilike(value)
                )
                if nomenclature is not None:
                    yield f"\nLa nomenclature {nomenclature.id_nomenclature} a été trouvée par cd_nomenclature"
                else:
                    nomenclature = get_nomenclature(
                        nomenclature_type, TNomenclatures.mnemonique.ilike(value)
                    )
                    if nomenclature is not None:
                        yield f"\nLa nomenclature '{nomenclature.id_nomenclature}' a été trouvée par mnemonique"
                if nomenclature is not None:
                    yield f"\n  mnemonique: {nomenclature.mnemonique}"
                    yield f"\n  cd_nomenclature: {nomenclature.cd_nomenclature}"
                    yield f"\n  label_default: {nomenclature.label_default}"
                    yield f"\n  label_fr: {nomenclature.label_fr}"
                    yield f"\n  definition_default: {nomenclature.definition_default}"
                    yield f"\n  definition_fr: {nomenclature.definition_fr}"
                    if fix and click.confirm("Utiliser ?"):
                        updated_value = nomenclature.id_nomenclature
                    else:
                        return value
            else:
                return value
        else:
            nomenclature = get_nomenclature(nomenclature_type, id_nomenclature=value)
            if nomenclature is None:
                yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - valeur '{value}' : non trouvée"
                return value

        if nomenclature is None:
            return value

        cd_nomenclatures = self.config.get("cd_nomenclatures")
        if cd_nomenclatures and nomenclature.cd_nomenclature not in cd_nomenclatures:
            yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - cd_nomenclature '{nomenclature.cd_nomenclature}' : non autorisée"
            yield "\nValeurs admises :"
            for cd_nomenclature in cd_nomenclatures:
                yield f"\n  {cd_nomenclature}"

        return value


class TaxonomyAdapter(BaseAdapter):
    key = "taxonomy"

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        type = fields.Str(validate=validate.Equal("taxonomy"))

    def get_default_widget(self, data, **kwargs):
        from .widgets import TaxonomyWidget

        return TaxonomyWidget(data, **kwargs)

    def get_wire_type(self):
        return int


# TODO: uuid, date, types_site, module, dataset, site, habitat, sites_group, area
# TODO: observer_list, taxonomy_list, municipality? accepté par la route util/<type_util>/
