from typing import Any
from functools import cache, cached_property

import click
import sqlalchemy as sa
from sqlalchemy import select
import marshmallow as ma
from marshmallow import (
    fields,
    validates_schema,
    ValidationError,
    post_load,
    validate,
    validates,
    pre_load,
)

from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring.tools.utils import schema_context

from .core import BaseAdapter


@cache
def get_nomenclature_type(mnemonique):
    return db.session.execute(
        select(BibNomenclaturesTypes).where(BibNomenclaturesTypes.mnemonique == mnemonique)
    ).scalar_one_or_none()


@cache
def get_nomenclature(nomenclature_type, *whereclauses, **kwargs):
    if nomenclature_type is not None:
        whereclauses = (TNomenclatures.nomenclature_type == nomenclature_type, *whereclauses)
    return db.session.execute(
        select(TNomenclatures).where(
            *whereclauses,
            *[getattr(TNomenclatures, k) == v for k, v in kwargs.items()],
        )
    ).scalar_one_or_none()


class NomenclatureAdapter(BaseAdapter):
    key = "nomenclature"

    @cache
    @staticmethod
    def get_types_mnemoniques():
        return list(db.session.execute(sa.select(BibNomenclaturesTypes.mnemonique)).scalars())

    @cache
    @staticmethod
    def get_nomenclature_columns():
        return sa.inspect(TNomenclatures).columns

    @classmethod
    def get_config_schema_class(cls):
        columns = NomenclatureAdapter.get_nomenclature_columns()

        class ConfigSchema(ma.Schema):
            class Meta:
                unknown = ma.RAISE

            type = fields.Str(validate=validate.Equal("nomenclature"))
            nomenclature_type = fields.Str(required=True)  # TODO: required à confirmer
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
                ctx = schema_context.get()
                if "nomenlature_type" in data and ctx and ctx.get("protocol_installed", False):
                    nomenclature_type = get_nomenclature_type(data["nomenclature_type"])
                    if nomenclature_type is None:
                        raise ValidationError(
                            f"'{data["nomenclature_type"]}' is not a valid nomenclature type mnemonique"
                        )
                    data["nomenclature_type"] = nomenclature_type
                return data

        return ConfigSchema

    def _get_default_widget(self, data, **kwargs):
        from ..widgets import NomenclatureWidget

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
        elif self.storage_col and isinstance(value, self.storage_type):  # FIXME: ok with list?
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
