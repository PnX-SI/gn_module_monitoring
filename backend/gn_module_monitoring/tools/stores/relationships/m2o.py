import logging
from functools import cache

import click
import sqlalchemy as sa
from sqlalchemy.orm import ColumnProperty
from marshmallow import ValidationError
from flask import current_app

from geonature.utils.env import db
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from gn_module_monitoring import MODULE_CODE

from .cache import get_instance
from .core import BaseRelationshipStore
from .mixin import AreaMixin, DatasetMixin, ModuleMixin, NomenclatureMixin, UserMixin
from .utils import (
    get_nomenclature,
    validate_areas_of_type,
    validate_observers_in_list,
)

log = logging.getLogger(__name__)


class BaseForeignKeyStore(BaseRelationshipStore):
    """
    Store pour une relation many-to-one : le champ est une foreign key.

    Asymétrie volontaire entre les deux sens :
    - chargement (API → DB) : `Field._deserialize` renvoie une instance, et `to_json_storage` la reçoit,
      car la validation (CEL, contrôles propres au store) en a besoin ;
    - dump (DB → API) : `from_json_storage` renvoie une clé primaire, et `Field._serialize` la reçoit,
      sans charger l’instance.
    """

    # Le store stocke la clé primaire de la cible (entier)
    sql_type = sa.types.Integer

    class Field(BaseRelationshipStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            """
            La valeur reçue de l'API est la clé primaire de la cible.
            Vérifie son type et l'existence de la ligne, puis retourne l’instance.
            """
            if value is None:
                return None
            store = self.store
            pk = store.get_model_pk()
            if not isinstance(value, pk.type.python_type):
                raise ValidationError(
                    f"Valeur '{value}' invalide : {pk.type.python_type.__name__} attendu."
                )
            instance = get_instance(store.get_model(), value)
            if instance is None:
                raise ValidationError(
                    f"Aucune instance de {store.get_model().__name__} pour {pk.name} = '{value}'."
                )
            return instance

    @classmethod
    def is_suitable_for_column(cls, column):
        return (
            len(fks := column.foreign_keys) == 1
            and next(iter(fks)).target_fullname == cls.fk_target
        )

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        if current_app.config[MODULE_CODE]["STRICT"] and self.native_attr is not None:
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
                raise ValidationError({self.field_name: error_message})

    def to_native_storage(self, value):
        """
        Écriture de l'attribut natif : une FK colonne reçoit la clé primaire de l'objet. Une relation
        (objet attendu par SQLAlchemy) reçoit l'objet.
        """
        if value is None or not isinstance(self.native_attr, ColumnProperty):
            return value
        return getattr(value, self.get_model_pk().name)

    def to_json_storage(self, value):
        if value is None:
            return None
        return self._to_storage(value)

    def from_json_storage(self, value):
        # Renvoie la clé primaire sans charger l’instance
        if value is None:
            return None
        return self._from_storage(value)

    def get_api_type(self) -> type:
        # Clé primaire de la cible : un identifiant entier
        return int

    def get_python_type(self) -> type:
        return self.get_model()


class UserStore(UserMixin, BaseForeignKeyStore):
    key = "user"
    fk_target = "utilisateurs.t_roles.id_role"

    class Field(BaseForeignKeyStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            instance = super()._deserialize(value, attr, data, **kwargs)
            if instance is not None and self.store.list:
                validate_observers_in_list([instance], self.store.list)
            return instance

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import UserWidget

        return UserWidget(data, **kwargs)


class ObserverListStore(BaseForeignKeyStore):
    key = "observer_list"
    model = "observer_list"
    fk_target = "utilisateurs.t_listes.id_liste"

    @classmethod
    def get_model(cls):
        from pypnusershub.db.models import UserList

        return UserList

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

        # TODO: instancier DatalistWidget avec les bon paramètres
        raise NotImplementedError("Missing default widget for adapter 'observer_list'")


class TaxonomyStore(BaseForeignKeyStore):
    key = "taxonomy"
    model = "taxonomy"
    fk_target = "taxonomie.taxref.cd_nom"

    @classmethod
    def get_model(cls):
        from apptax.taxonomie.models import Taxref

        return Taxref

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import TaxonomyWidget

        return TaxonomyWidget(data, **kwargs)


class TaxonomyListStore(BaseForeignKeyStore):
    key = "taxonomy_list"
    model = "taxonomy_list"
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
                **(data or {}),
            },
            **kwargs,
        )


class DatasetStore(DatasetMixin, BaseForeignKeyStore):
    key = "dataset"
    fk_target = "gn_meta.t_datasets.id_dataset"

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatasetWidget

        return DatasetWidget(data, **kwargs)


class HabitatStore(BaseForeignKeyStore):
    key = "habitat"
    model = "habitat"
    fk_target = "ref_habitats.habref.cd_hab"

    @classmethod
    def get_model(cls):
        from pypn_habref_api.models import Habref

        return Habref

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import HabitatWidget

        return HabitatWidget(data, **kwargs)


class IndividualStore(BaseForeignKeyStore):
    key = "individual"
    model = "individual"
    fk_target = "gn_monitoring.t_individuals.id_individual"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringIndividuals

        return TMonitoringIndividuals

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import IndividualsWidget

        return IndividualsWidget(data, **kwargs)


class SitesGroupStore(BaseForeignKeyStore):
    key = "sites_group"
    model = "sites_group"
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
                **(data or {}),
            },
            **kwargs,
        )


class SiteStore(BaseForeignKeyStore):
    key = "site"
    model = "site"
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
                **(data or {}),
            },
            **kwargs,
        )


class VisitStore(BaseForeignKeyStore):
    key = "visit"
    model = "visit"
    fk_target = "gn_monitoring.t_base_visits.id_base_visit"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringVisits

        return TMonitoringVisits

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import DatalistWidget

        return DatalistWidget(
            {
                "attribut_label": "Visite",
                "keyValue": "id_base_visit",
                "keyLabel": "visit_date_min",
                "multiple": False,
                "api": "monitorings/visits",
                **(data or {}),
            },
            **kwargs,
        )


class ModuleStore(ModuleMixin, BaseForeignKeyStore):
    key = "module"
    fk_target = "gn_commons.t_modules.id_module"

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import ModuleWidget

        return ModuleWidget(
            {"attribut_label": "Modules", **(data or {}), "multiple": False}, **kwargs
        )


class AreaStore(AreaMixin, BaseForeignKeyStore):
    key = "area"
    fk_target = "ref_geo.l_areas.id_area"

    class Field(BaseForeignKeyStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            instance = super()._deserialize(value, attr, data, **kwargs)
            if instance is not None and self.store.area_type:
                validate_areas_of_type([instance], self.store.area_type)
            return instance

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import AreasWidget

        return AreasWidget({**(data or {}), "multiple": False}, **kwargs)


class NomenclatureStore(NomenclatureMixin, BaseForeignKeyStore):
    key = "nomenclature"

    fk_target = "ref_nomenclatures.t_nomenclatures.id_nomenclature"

    class Field(BaseForeignKeyStore.Field):
        def _deserialize(self, value, attr, data, **kwargs):
            instance = super()._deserialize(value, attr, data, **kwargs)
            if instance is not None:
                self.store.validate_nomenclatures_of_type([instance])
            return instance

    @cache
    @staticmethod
    def get_types_mnemoniques():
        return list(db.session.execute(sa.select(BibNomenclaturesTypes.mnemonique)).scalars())

    def _get_default_widget(self, data, **kwargs):
        from gn_module_monitoring.tools.widgets import NomenclatureWidget

        return NomenclatureWidget(data, **kwargs)

    def check_stored_value(self, entity, row_id, field_name, value, fix):
        # TODO: cette fonction s’attend uniquement à trouver un id_nomenclature
        # Il faut la faire évoluer pour gérer storage_col & storage_cols
        updated_value = value

        nomenclature_type = self.nomenclature_type

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
