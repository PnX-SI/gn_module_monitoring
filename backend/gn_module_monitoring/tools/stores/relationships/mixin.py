import sqlalchemy as sa
from marshmallow import (
    ValidationError,
    fields,
    post_dump,
    pre_load,
    validates,
    validates_schema,
)
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures
from pypnusershub.db.models import UserList
from ref_geo.models import BibAreasTypes
from sqlalchemy import select

from geonature.utils.env import db

from .core import BaseRelationshipStore
from .utils import get_declared_nomenclatures, get_nomenclature_type


class UserMixin:
    model = "user"
    fk_target = "utilisateurs.t_roles.id_role"

    class ConfigSchema(BaseRelationshipStore.ConfigSchema):
        # Code de la liste d’observateurs : si défini, l’utilisateur doit appartenir à cette liste.
        code_list = fields.Str()

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        self.list = None
        if code := self.get("code_list"):
            self.list = db.session.execute(
                sa.select(UserList).where(UserList.code_liste == code)
            ).scalar_one_or_none()
            if self.list is None:
                raise ValidationError({"code_list": f"La liste '{code}' n’existe pas."})

    @classmethod
    def get_model(cls):
        from pypnusershub.db.models import User

        return User


class DatasetMixin:
    model = "dataset"

    @classmethod
    def get_model(cls):
        from geonature.core.gn_meta.models import TDatasets

        return TDatasets


class NomenclatureMixin:
    model = "nomenclature"

    class ConfigSchema(BaseRelationshipStore.ConfigSchema):
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
                data["nomenclature_type"] = data["api"].split("/")[2]
            return data

        @validates("nomenclature_type")
        def validate_nomenclature_type(self, value, **kwargs):
            # On valide nomenclature_type avant que soit validé les cd_nomenclatures
            # Le type doit exister en base OU être déclaré dans le nomenclature.json du module
            declared_types = {t["mnemonique"] for t in get_declared_nomenclatures()["types"]}
            if get_nomenclature_type(value) is None and value not in declared_types:
                raise ValidationError(f"Le type de nomenclature '{value} n’existe pas.")

        @post_dump
        def dump_code_nomenclature_type(self, data, **kwargs):
            # Le frontend attend le mnémonique du type (et non son code …) dans `code_nomenclature_type`
            data["code_nomenclature_type"] = data.pop("nomenclature_type")
            return data

        @validates_schema
        def validate_cd_nomenclatures(self, data, **kwargs):
            # Vérifie que chaque cd_nomenclature existe pour le type de nomenclature demandé,
            # en base OU dans le nomenclature.json du module.
            # Si nomenclature_type est absent ou inconnu, c'est signalé ailleurs : on ne vérifie rien.
            type_mnemonique = data["nomenclature_type"]
            if "cd_nomenclatures" not in data:
                return
            cd_nomenclatures = data["cd_nomenclatures"]
            # nomenclatures existantes en base
            existing_nomenclatures = set(
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
            # nomenclatures déclarées dans nomenclature.json
            declared_nomenclatures = {
                n["cd_nomenclature"]
                for n in get_declared_nomenclatures()["nomenclatures"]
                if n["type"] == type_mnemonique
            }
            missing = [
                cd
                for cd in cd_nomenclatures
                if cd not in existing_nomenclatures and cd not in declared_nomenclatures
            ]
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

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        mnemonique = self["nomenclature_type"]
        # Un type déclaré seulement dans le nomenclature.json n’existe pas encore en base
        self.nomenclature_type = get_nomenclature_type(mnemonique) or BibNomenclaturesTypes(
            mnemonique=mnemonique
        )

    def _get_storage_filters(self):
        # Un cd_nomenclature n'est unique qu'au sein de son type
        return [TNomenclatures.id_type == self.nomenclature_type.id_type]

    @classmethod
    def get_model(cls):
        from pypnnomenclature.models import TNomenclatures

        return TNomenclatures


class ModuleMixin:
    model = "module"

    @classmethod
    def get_model(cls):
        from gn_module_monitoring.monitoring.models import TMonitoringModules

        return TMonitoringModules


class AreaMixin:
    model = "area"

    class ConfigSchema(BaseRelationshipStore.ConfigSchema):
        # Code du type de zone (ref_geo.bib_areas_types.type_code) : si défini, seules les zones
        # de ce type sont acceptées.
        area_code = fields.Str()

    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
        self.area_type = None
        if type_code := self.get("area_code"):
            self.area_type = db.session.execute(
                sa.select(BibAreasTypes).where(BibAreasTypes.type_code == type_code)
            ).scalar_one_or_none()
            if self.area_type is None:
                raise ValidationError(
                    {"area_code": f"Le type de zone '{type_code}' n’existe pas."}
                )

    @classmethod
    def get_model(cls):
        from ref_geo.models import LAreas

        return LAreas
