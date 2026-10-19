import logging
from functools import cache
from typing import Any

import click
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from marshmallow import (
    fields,
    validate,
    validates,
    validates_schema,
    ValidationError,
    post_load,
    pre_load,
)
from flask import current_app

from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.tools.utils import schema_context

from .core import BaseRelationshipStore
from .utils import get_nomenclature, get_nomenclature_type

log = logging.getLogger(__name__)


class BaseForeignKeyStore(BaseRelationshipStore):
    """
    Store pour une relation many-to-one : le champ est une foreign key.
    """

    class ConfigSchema(BaseRelationshipStore.ConfigSchema):
        pass

    @classmethod
    def is_suitable_for_column(cls, column):
        return (
            len(fks := column.foreign_keys) == 1
            and next(iter(fks)).target_fullname == cls.fk_target
        )

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        if self.native_attr is not None:
            # Cas attendu : une colonne simple, portant une FK unique vers self.fk_target
            error_message = None
            if (
                not isinstance(self.native_attr, ColumnProperty)
                or len(self.native_attr.columns) != 1
            ):
                error_message = f"Le store {self.key} doit être utilisé avec une colonne simple."
            else:
                fks = self.native_attr.columns[0].foreign_keys
                if len(fks) != 1:
                    error_message = f"Le store {self.key} doit être utilisé avec une FK simple."
                else:
                    target = next(iter(fks)).target_fullname
                    if target != self.fk_target:
                        error_message = (
                            f"Le store {self.key} doit être utilisé avec une FK vers {self.fk_target}. "
                            f"Trouvé une FK vers {target}."
                        )
            if error_message is not None:
                if current_app.config[MODULE_CODE]["STRICT"]:
                    raise ValidationError({self.field_name: error_message})
                else:
                    log.warning(f"Validation warning: {error_message}")

    def get_instance_by_col(self, value):
        """
        Lorsque storage_col est renseigné, cette fonction va récupérer l’instance du modèle.
        """
        try:
            return db.session.execute(
                sa.select(self.get_model()).where(
                    self.get_model_attrs()[self.storage_col] == value
                )
            ).scalar_one()
        except NoResultFound:
            raise ValueError(f"Unexpected value '{value}' : aucune instance trouvée.")
        except MultipleResultsFound:
            raise ValueError(f"Unexpected value '{value}' : plusieurs instances trouvées.")

    def wire_to_storage(self, value: Any) -> Any:
        """
        La valeur reçue de l'API est la clé primaire de la cible.
        Vérifie son type et l'existence de la ligne, puis retourne la valeur à stocker.
        """
        if value is None:
            return None
        pk = self.get_model_pk()
        if not isinstance(value, pk.type.python_type):
            raise ValidationError(
                f"Valeur '{value}' invalide : {pk.type.python_type.__name__} attendu."
            )
        if db.session.get(self.get_model(), value) is None:
            raise ValidationError(
                f"Aucune instance de {self.get_model().__name__} pour {pk.name} = '{value}'."
            )
        return value

    def storage_to_wire(self, value: Any) -> Any:
        if value is None:
            return None
        elif self.get("storage_cols") and isinstance(value, dict):
            return value[self.get_model_pk().name]
        elif self.get("storage_col") and isinstance(
            value, self.get_model_attrs[self.get("storage_col")].type.python_type
        ):
            return getattr(self.get_instance_by_col(value), self.get_model_pk().name)
        elif (pk := self.get_model_pk()) is not None and isinstance(value, pk.type.python_type):
            return value  # we assume this is the pk!
        else:
            raise ValueError(f"Unexpected value '{value}'")


class UserStore(BaseForeignKeyStore):
    key = "user"
    fk_target = "utilisateurs.t_roles.id_role"

    @classmethod
    def get_model(cls):
        from pypnusershub.db.models import User

        return User

    class ConfigSchema(BaseForeignKeyStore.ConfigSchema):
        multiple = fields.Bool(load_default=False)

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import UserWidget

        return UserWidget(data, **kwargs)

    def get_wire_type(self):
        if self["multiple"]:
            return list[int]
        return int


class ObserverListStore(BaseForeignKeyStore):
    key = "observer_list"
    fk_target = "utilisateurs.t_listes.id_liste"

    @classmethod
    def get_model(cls):
        from pypnusershub.db.models import UserList

        return UserList

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

        # TODO: instancier DatalistWidget avec les bon paramètres
        raise NotImplementedError("Missing default widget for adapter 'observer_list'")

    def get_wire_type(self):
        return list[int]


class TaxonomyStore(BaseForeignKeyStore):
    key = "taxonomy"
    fk_target = "taxonomie.taxref.cd_nom"

    @classmethod
    def get_model(cls):
        from apptax.taxonomie.models import Taxref

        return Taxref

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TaxonomyWidget

        return TaxonomyWidget(data, **kwargs)

    def get_wire_type(self):
        return int


class TaxonomyListStore(BaseForeignKeyStore):
    key = "taxonomy_list"
    fk_target = "taxonomie.bib_listes.id_liste"

    @classmethod
    def get_model(cls):
        from apptax.taxonomie.models import BibListes

        return BibListes

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Liste des taxons",
                "keyValue": "id_liste",
                "keyLabel": "nom_liste",
                "multiple": False,
                "api": "biblistes/",
            },
            **kwargs,
        )

    def get_wire_type(self):
        return int


class DatasetStore(BaseForeignKeyStore):
    key = "dataset"
    fk_target = "gn_meta.t_datasets.id_dataset"

    @classmethod
    def get_model(cls):
        from geonature.core.gn_meta.models import TDatasets

        return TDatasets

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatasetWidget

        return DatasetWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        return int


class HabitatStore(BaseForeignKeyStore):
    key = "habitat"
    fk_target = "ref_habitats.habref.cd_hab"

    @classmethod
    def get_model(cls):
        from pypn_habref_api.models import Habref

        return Habref

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import HabitatWidget

        return HabitatWidget(data, **kwargs)

    def get_wire_type(self) -> type:
        return int


class SitesGroupStore(BaseForeignKeyStore):
    key = "sites_group"
    fk_target = "gn_monitoring.t_sites_groups.id_sites_group"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringSitesGroups

        return TMonitoringSitesGroups

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Groupe de sites",
                "keyValue": "id_sites_group",
                "keyLabel": "sites_group_name",
                "multiple": False,
                "api": "monitorings/sites_groups",
            },
            **kwargs,
        )

    def get_wire_type(self) -> type:
        return int


class SiteStore(BaseForeignKeyStore):
    key = "site"
    fk_target = "gn_monitoring.t_base_sites.id_base_site"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringSites

        return TMonitoringSites

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Site",
                "keyValue": "id_base_site",
                "keyLabel": "base_site_name",
                "multiple": False,
                "api": "monitorings/sites",
            },
            **kwargs,
        )

    def get_wire_type(self) -> type:
        return int


class ModuleStore(BaseForeignKeyStore):
    key = "module"
    fk_target = "gn_commons.t_modules.id_module"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringModules

        return TMonitoringModules

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import ModuleWidget

        return ModuleWidget(
            {"attribut_label": "Modules", **(data or {}), "multiple": False}, **kwargs
        )

    def get_wire_type(self) -> type:
        return list[int]


class NomenclatureStore(BaseForeignKeyStore):
    key = "nomenclature"

    @classmethod
    def get_model(cls):
        from pypnnomenclature.models import TNomenclatures

        return TNomenclatures

    fk_target = "ref_nomenclatures.t_nomenclatures.id_nomenclature"

    @cache
    @staticmethod
    def get_types_mnemoniques():
        return list(db.session.execute(sa.select(BibNomenclaturesTypes.mnemonique)).scalars())

    class ConfigSchema(BaseForeignKeyStore.ConfigSchema):
        nomenclature_type = fields.Str(required=True)
        cd_nomenclatures = fields.List(fields.Str())

        @pre_load
        def retrocompat(self, data, **kwargs):
            # it is a mnemonique, not a code, so the field was renamed
            if "code_nomenclature_type" in data:
                data["nomenclature_type"] = data.pop("code_nomenclature_type")
            if "value" in data:  # TODO: this is kind of a way to define a default value?
                if "code_nomenclature_type" in data["value"]:
                    data["nomenclature_type"] = data["value"]["code_nomenclature_type"]
                if "cd_nomenclature" in data["value"]:
                    data["cd_nomenclatures"] = [data["value"]["cd_nomenclature"]]
            # find nomenclature_type from datalist widget api url (better to use nomenclature widget…)
            if (
                "nomenclature_type" not in data
                and data.get("type_widget") == "datalist"
                and data.get("api", "").startswith("nomenclatures/nomenclature/")
            ):
                # ctx = schema_context.get()
                # log.warning(
                #     f"{ctx["entity"].name} - {ctx["field_name"]} - "
                #     "Detected nomenclature store with datalist widget. "
                #     "Consider using nomenclature widget."
                # )
                data["nomenclature_type"] = data["api"].split("/")[2]
            return data

        @validates("nomenclature_type")
        def validate_nomenclature_type(self, value, **kwargs):
            # On valide nomenclature_type avant que soit validé les cd_nomenclatures
            # N’est validé que pour les protocoles installés !
            ctx = schema_context.get()
            if not ctx.get("protocol_installed", True):
                return
            if get_nomenclature_type(value) is None:
                raise ValidationError(f"Le type de nomenclature '{value} n’existe pas.")
            # TODO: vérifier qu’elle existe en base OU qu’elle est déclarer dans nomenclature.json ?

        @validates_schema
        def validate_cd_nomenclatures(self, data, **kwargs):
            # Vérifie que chaque cd_nomenclature existe pour le type de nomenclature demandé.
            # Si nomenclature_type est absent ou inconnu, c'est signalé ailleurs : on ne vérifie rien.
            # N’est validé que pour les protocoles installés !
            ctx = schema_context.get()
            if not ctx.get("protocol_installed", True):
                return
            type_mnemonique = data["nomenclature_type"]
            if "cd_nomenclatures" not in data:
                return
            cd_nomenclatures = data["cd_nomenclatures"]
            found = set(
                db.session.execute(
                    select(TNomenclatures.cd_nomenclature)
                    .join(
                        BibNomenclaturesTypes,
                        TNomenclatures.id_type == BibNomenclaturesTypes.id_type,
                    )
                    .where(
                        BibNomenclaturesTypes.mnemonique == type_mnemonique,
                        TNomenclatures.cd_nomenclature.in_(cd_nomenclatures),
                    )
                ).scalars()
            )
            missing = [cd for cd in cd_nomenclatures if cd not in found]
            if missing:
                raise ValidationError(
                    {
                        "cd_nomenclatures": f"Les cd_nomenclature {missing} n'existent pas pour le type de nomenclature '{type_mnemonique}'."
                    }
                )

        @validates_schema
        def set_defaults(self, data, **kwargs):
            # Par défaut, on stock ces 3 colonnes de la nomenclature
            if "storage_col" not in data and "storage_cols" not in data:
                data["storage_cols"] = ["id_nomenclature", "cd_nomenclature", "label_default"]

        @post_load
        def load_nomenclature_type(self, data, **kwargs):
            data["nomenclature_type"] = get_nomenclature_type(data["nomenclature_type"])
            return data

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NomenclatureWidget

        return NomenclatureWidget(data, **kwargs)

    def get_wire_type(self):
        return int

    def storage_to_wire(self, value: Any) -> Any:
        try:
            super().storage_to_wire(value)
        except ValueError:
            if self.storage_col and isinstance(
                value, self.get_model_attrs()[self.storage_col].type.python_type
            ):
                nomenclature = get_nomenclature(
                    type=self["nomenclature_type"], **{self.storage_col: value}
                )
                if nomenclature is not None:
                    return nomenclature
            # Pas de solution trouvé
            raise

    def check_stored_value(self, entity, row_id, field_name, value, fix):
        # TODO: cette fonction s’attend uniquement à trouver un id_nomenclature
        # Il faut la faire évoluer pour gérer storage_col & storage_cols
        updated_value = value

        nomenclature_type = self["nomenclature_type"]

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

        cd_nomenclatures = self.get("cd_nomenclatures")
        if cd_nomenclatures and nomenclature.cd_nomenclature not in cd_nomenclatures:
            yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - cd_nomenclature '{nomenclature.cd_nomenclature}' : non autorisée"
            yield "\nValeurs admises :"
            for cd_nomenclature in cd_nomenclatures:
                yield f"\n  {cd_nomenclature}"

        return value
