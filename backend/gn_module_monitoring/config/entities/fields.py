from copy import deepcopy
from typing import Any
import logging

import marshmallow as ma
from marshmallow import fields, pre_load, post_load, ValidationError
from flask import current_app

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.tools.widgets import (
    DatasetWidget,
    TextWidget,
    TextareaWidget,
    CheckboxWidget,
    RadioWidget,
    NumberWidget,
    DateWidget,
    TimeWidget,
    SelectWidget,
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
    BaseStore,
    StringStore,
    BooleanStore,
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

logger = logging.getLogger()


class WidgetConfigSchema(ma.Schema):
    widget_map = {
        TextWidget.key: TextWidget,
        TextareaWidget.key: TextareaWidget,
        CheckboxWidget.key: CheckboxWidget,
        RadioWidget.key: RadioWidget,
        NumberWidget.key: NumberWidget,
        DateWidget.key: DateWidget,
        TimeWidget.key: TimeWidget,
        SelectWidget.key: SelectWidget,
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
        BooleanStore.key: BooleanStore,
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

    # Widget & store created in @post_load so using raw fields
    widget = fields.Raw()
    store = fields.Raw()

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
        orig_data = deepcopy(data)
        if "type_widget" in data:
            if "widget" in data:
                raise ValidationError(
                    {"widget": "Vous devez supprimer 'type_widget' lorsque vous utilisez 'widget'"}
                )
            widget_type = data.pop("type_widget")
            data["widget"] = deepcopy(orig_data)
            data["widget"]["type"] = widget_type
        if "type_util" in data:
            if "store" in data:
                raise ValidationError(
                    {"store": "Vous devez supprimer 'type_util' lorsque vous utilisez 'store'"}
                )
            store_type = data.pop("type_util")
            data["store"] = deepcopy(orig_data)
            data["store"]["type"] = store_type
        return data

    @post_load
    def post_load(self, data, **kwargs):
        widget_init = False
        # Le widget est définie avec un type, initialisation
        if "type" in data.get("widget", {}):
            data["widget"] = WidgetConfigSchema().load(data["widget"])
            widget_init = True

        # Initialisation du store :
        # - à partir de son type
        # - à partir du widget
        # - à partir du type de la colonne SQL
        # FIXME: inverse priority between widget & sql column?
        if "type" in data.get("store", {}):
            data["store"] = StoreConfigSchema().load(data["store"])
        elif widget_init:
            try:
                data["store"] = data["widget"].get_default_store(data.get("store"))
            except ValidationError as e:
                raise ValidationError({"store": e.messages_dict})
        else:
            from gn_module_monitoring.services import SERVICE_MAP

            ctx = schema_context.get()
            entity = SERVICE_MAP[ctx["entity"]]
            field_name = ctx["field_name"]
            column = entity.get_columns().get(field_name)
            if column:
                try:
                    data["store"] = BaseStore.get_store_from_column_attr(column)(data.get("store"))
                except ValueError as e:
                    raise ValidationError(
                        {"store": f"{e}. Définissez explicitement un store et son type."}
                    )
            else:
                raise ValidationError("Vous devez fournir 'store' ou 'widget'")

        # At this point, the store exists.

        # Instanciation du widget à partir du store
        if not widget_init:
            try:
                data["widget"] = data["store"].get_default_widget(data.get("widget"))
            except ValidationError as e:
                raise ValidationError({"widget": e.messages_dict})

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
            message = f"Incohérence de type : {data["widget"]} renvoit '{widget_wire_type}' alors que {data["store"]} attend '{store_wire_type}'"
            if current_app.config[MODULE_CODE]["STRICT"]:
                raise ValidationError(message)
            else:
                logger.warning(message)

        return data
