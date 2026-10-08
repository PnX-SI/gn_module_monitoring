from typing import Literal, Never, Any

import marshmallow as ma
from marshmallow import fields, validate

from gn_module_monitoring.command.check.utils import ValueLabelField


class BaseAdapter:
    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

    def __init__(self, data=None, **kwargs):
        self.config = self.ConfigSchema().load(data or {}, **kwargs)

    def get_default_widget(self, data, **kwargs):
        raise NotImplementedError

    def wire_to_storage(self):
        pass

    def storage_to_wire(self):
        pass

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

    class ConfigSchema(ma.Schema):
        class Meta:
            unknown = ma.RAISE

        type = fields.Str(validate=validate.Equal("nomenclature"))

    def get_default_widget(self, data, **kwargs):
        from .widgets import NomenclatureWidget

        return NomenclatureWidget(data, **kwargs)

    def get_wire_type(self):
        return int

    def check_value(self, row_id, field_name, value, fix):
        from .nomenclature import get_nomenclature_type, get_nomenclature

        updated_value = None

        mnemonique = field_conf.get("code_nomenclature_type")
        if mnemonique is None:
            yield f"Missing mnemonique in field '{field_name}' config"
            return
        nomenclature_type = get_nomenclature_type(mnemonique)
        if nomenclature_type is None:
            yield f"Nomenclature type not found for mnemonique '{mnemonique}'"
            return

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
                        return
            else:
                return
        else:
            nomenclature = get_nomenclature(nomenclature_type, id_nomenclature=value)
            if nomenclature is None:
                yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - valeur '{value}' : non trouvée"
                return

        if nomenclature is None:
            return

        cd_nomenclatures = field_conf.get("cd_nomenclatures")
        if cd_nomenclatures and nomenclature.cd_nomenclature not in cd_nomenclatures:
            yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - cd_nomenclature '{nomenclature.cd_nomenclature}' : non autorisée"
            yield "\nValeurs admises :"
            for cd_nomenclature in cd_nomenclatures:
                yield f"\n  {cd_nomenclature}"

        return updated_value


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
