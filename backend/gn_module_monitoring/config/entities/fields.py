from copy import deepcopy
from functools import cache
from typing import Any

import sqlalchemy as sa
import marshmallow as ma
from marshmallow import fields, pre_load, post_load, validates_schema, ValidationError

from gn_module_monitoring.tools.widgets import (
    DatasetWidget,
    TextWidget,
    TextareaWidget,
    CheckboxWidget,
    RadioWidget,
    NumberWidget,
    DateWidget,
    TimeWidget,
    MultiselectWidget,
    DatalistWidget,
    NomenclatureWidget,
    TaxonomyWidget,
    HabitatWidget,
    MediaWidget,
    UserWidget,
    ObserversWidget,
    ObserversTextWidget,
    AreasWidget,
)
from gn_module_monitoring.tools.stores import (
    StringStore,
    UserStore,
    ObserverListStore,
    NomenclatureStore,
    TaxonomyStore,
    TaxonomyListStore,
    DatasetStore,
    HabitatStore,
    TypesSiteStore,
    ModuleStore,
    UUIDStore,
    AreasStore,
)
from gn_module_monitoring.tools.utils import MultilineStr, schema_context


class WidgetConfigSchema(ma.Schema):
    widget_map = {
        TextWidget.key: TextWidget,
        TextareaWidget.key: TextareaWidget,
        CheckboxWidget.key: CheckboxWidget,
        RadioWidget.key: RadioWidget,
        NumberWidget.key: NumberWidget,
        DateWidget.key: DateWidget,
        TimeWidget.key: TimeWidget,
        MultiselectWidget.key: MultiselectWidget,
        DatalistWidget.key: DatalistWidget,
        NomenclatureWidget.key: NomenclatureWidget,
        TaxonomyWidget.key: TaxonomyWidget,
        UserWidget.key: UserWidget,
        ObserversWidget.key: ObserversWidget,
        ObserversTextWidget.key: ObserversTextWidget,
        DatasetWidget.key: DatasetWidget,
        HabitatWidget.key: HabitatWidget,
        MediaWidget.key: MediaWidget,
        ObserversTextWidget.key: ObserversTextWidget,
        AreasWidget.key: AreasWidget,
    }

    type = fields.Str(required=True)

    def load(self, data, **kwargs):
        data = super().load(data, unknown=ma.INCLUDE)
        if data["type"] in self.widget_map:
            widget = self.widget_map[data["type"]]
            return widget(data, **kwargs)
        else:
            raise ValidationError(
                {
                    "type": f"Type de widget '{data["type"]}' inconnu. Types autorisés : {', '.join(self.widget_map)}"
                }
            )


class StoreConfigSchema(ma.Schema):
    store_map = {
        UserStore.key: UserStore,
        ObserverListStore.key: ObserverListStore,
        NomenclatureStore.key: NomenclatureStore,
        TaxonomyStore.key: TaxonomyStore,
        TaxonomyListStore.key: TaxonomyListStore,
        DatasetStore.key: DatasetStore,
        HabitatStore.key: HabitatStore,
        TypesSiteStore.key: TypesSiteStore,
        ModuleStore.key: ModuleStore,
        UUIDStore.key: UUIDStore,
        AreasStore.key: AreasStore,
        "area": (AreasStore, {"many": False}),
    }

    type = fields.Str(required=True)

    def load(self, data, **kwargs):
        data = super().load(data, unknown=ma.INCLUDE)
        if data["type"] in self.store_map:
            store = self.store_map[data["type"]]
            if type(store) == tuple:
                store, default_params = store
            else:
                default_params = {}
            return store(data, **{**default_params, **kwargs})
        else:
            raise ValidationError(
                {
                    "type": f"Type de store '{data["type"]}' inconnu. Types autorisés : {', '.join(self.store_map)}"
                }
            )


class EntityFieldConfigSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE  # TODO: switch to raise once schema complete

    # FIXME: actuellement, on peut spécifier que le widget (resp. le store) auquel cas le store (resp. le widget) est déterminé automatiquement.
    # Comment utiliser, pour un widget donnée, le store par défaut, mais overrider certaines propriétés ?
    widget = fields.Nested(WidgetConfigSchema)
    store = fields.Nested(StoreConfigSchema)

    required = fields.Boolean(load_default=False)
    required_js = MultilineStr()
    hidden = fields.Boolean(load_default=False)
    hidden_js = MultilineStr()

    def load(self, data, **kwargs):
        with schema_context(field_name=data.pop("name")):
            return super().load(data, **kwargs)

    @pre_load
    def pre_load(self, data, **kwargs):
        # Si required (resp. hidden) n'est pas un booléen, c'est une valeur dynamique à évaluer en js.
        # On considère le champs commen non requis (resp. non masqué) en l'absence de possibilité de savoir ce qu'il en est réellement.
        if "required" in data and not isinstance(data["required"], bool):
            data["required_js"] = data.pop("required")
            data["required"] = False
        if "hidden" in data and not isinstance(data["hidden"], bool):
            data["hidden_js"] = data.pop("hidden")
            data["hidden"] = False
        # retro-compat.
        if "type_widget" in data:
            # TODO: gérer le mélange type_widget + widget due à générique + spécifique
            data["widget"] = deepcopy(data)
            data["widget"]["type"] = data.pop("type_widget")
        if "type_util" in data:
            # TODO: gérer le mélange type_util + store due à générique + spécifique
            data["store"] = deepcopy(data)
            data["store"]["type"] = data.pop("type_util")
        return data

    @post_load(pass_original=True)
    def post_load(self, data, original_data, **kwargs):
        # Instanciation du store à partir du widget
        if "widget" in data and "store" not in data:
            try:
                data["store"] = data["widget"].get_default_store()
            except ValidationError as e:
                raise ValidationError({"store": e.messages_dict})
        # Instanciation du widget à partir du store
        if "store" in data and "widget" not in data:
            try:
                data["widget"] = data["store"].get_default_widget()
            except ValidationError as e:
                raise ValidationError({"widget": e.messages_dict})
        elif "widget" not in data and "store" not in data:
            data["widget"] = TextWidget()
            data["store"] = StringStore()

        # Vérification de la cohérence des données entre le widget et le store.
        # Si l'un des deux renvoit None, cela veut dire que le type n'est pas connue
        # (typiquement datalist qui ne connait pas le type de retour de l'API)
        # et dans ce cas la vérification ne peut pas avoir lieu.
        widget_wire_type = data["widget"].get_wire_type()
        store_wire_type = data["store"].get_wire_type()
        if (
            widget_wire_type != store_wire_type
            and widget_wire_type is not Any
            and store_wire_type is not Any
        ):
            raise ValidationError(
                f"Incohérence de type : {data["widget"]} renvoit '{widget_wire_type}' alors que {data["store"]} attend '{store_wire_type}'"
            )

        return data
