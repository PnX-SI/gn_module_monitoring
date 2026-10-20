from copy import copy, deepcopy
from typing import Any
import logging

import marshmallow as ma
from marshmallow import (
    fields,
    pre_load,
    post_load,
    pre_dump,
    post_dump,
    validates,
    validates_schema,
    ValidationError,
)
from flask import current_app

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.tools.widgets import WIDGET_MAP
from gn_module_monitoring.tools.stores import BaseStore, STORE_MAP
from gn_module_monitoring.tools.utils import (
    CELValidationsField,
    check_cel_syntax,
    schema_context,
)

logger = logging.getLogger()


class WidgetConfigSchema(ma.Schema):
    type = fields.Str(required=True)

    def load(self, data, **kwargs):
        data = super().load(data, unknown=ma.INCLUDE)
        if data["type"] in WIDGET_MAP:
            widget = WIDGET_MAP[data["type"]]
            return widget(data, **kwargs)
        else:
            raise ValidationError(
                {
                    "type": f"Type de widget '{data["type"]}' inconnu. Types autorisés : {', '.join(WIDGET_MAP)}"
                }
            )


class StoreConfigSchema(ma.Schema):
    type = fields.Str(required=True)

    def load(self, data, **kwargs):
        data = super().load(data, unknown=ma.INCLUDE)
        if data["type"] in STORE_MAP:
            store = STORE_MAP[data["type"]]
            return store(data, **kwargs)
        else:
            raise ValidationError(
                {
                    "type": f"Type de store '{data["type"]}' inconnu. Types autorisés : {', '.join(STORE_MAP)}"
                }
            )


class EntityFieldConfigSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE  # TODO: switch to raise once schema complete

    # Widget & store created in @post_load so using raw fields
    widget = fields.Raw()
    store = fields.Raw()

    required = fields.Boolean()
    required_cel = fields.Str()
    validate_cel = CELValidationsField()

    @validates("required_cel")
    def validate_required_cel(self, value, **kwargs):
        check_cel_syntax(value)

    @validates_schema
    def validate_required_exclusive(self, data, **kwargs):
        if "required" in data and "required_cel" in data:
            raise ValidationError(
                "'required' et 'required_cel' ne peuvent pas être définis ensemble."
            )

    def load(self, data, **kwargs):
        with schema_context(field_name=data.pop("name")):
            return super().load(data, **kwargs)

    @pre_load
    def pre_load(self, data, **kwargs):
        # Si required (resp. hidden) n'est pas un booléen, c'est une valeur dynamique à évaluer en js que l’on transmet au widget.
        # On considère le champs comme non requis (resp. non masqué) en l'absence de possibilité de savoir ce qu'il en est réellement.
        if "required" in data and not isinstance(data["required"], bool):
            data.setdefault("widget", {})["required_js"] = data.pop("required")
            data["required"] = False

        # retro-compat.
        orig_data = deepcopy(data)
        if "type_widget" in data:
            if "widget" in data:
                data["widget"].update(data)
            else:
                data["widget"] = deepcopy(orig_data)
            widget_type = data.pop("type_widget")
            data["widget"]["type"] = widget_type
            if widget_type == "site":  # retro-compat
                # Il n’y a pas de widget site
                if not data["widget"].get("hidden", False):
                    raise ValidationError({"widget": "Le widget 'site' ne peut que être hidden."})
                data["widget"]["type"] = "hidden"
        if "type_util" in data:
            if "store" in data:
                data["store"].update(data)
            else:
                data["store"] = deepcopy(orig_data)
            store_type = data.pop("type_util")
            data["store"]["type"] = store_type
            if store_type == "dataset" and data["store"].pop("multi_select", False):
                data["store"]["type"] = "datasets"
            if store_type == "module" and data["store"].pop("multiple", False):
                data["store"]["type"] = "modules"
            if store_type == "user" and data["store"].pop("multi_select", False):
                data["store"]["type"] = "users"
        return data

    @post_load
    def post_load(self, data, **kwargs):
        # required, required_cel et validate_cel sont passés aux constructeurs, ils ne font pas
        # partie de la config
        field_kwargs = {
            key: data[key] for key in ("required", "required_cel", "validate_cel") if key in data
        }

        widget_init = False
        # Le widget est définie avec un type, initialisation
        if "type" in data.get("widget", {}):
            try:
                data["widget"] = WidgetConfigSchema().load(data["widget"], **field_kwargs)
                widget_init = True
            except ValidationError as e:
                raise ValidationError({"widget": e.messages_dict})

        # Initialisation du store :
        # - à partir de son type
        # - à partir du widget
        # - à partir du type de la colonne SQL
        # FIXME: inverse priority between widget & sql column?
        store_config = data.get("store") or {}
        if "type" in data.get("store", {}):
            try:
                data["store"] = StoreConfigSchema().load(store_config, **field_kwargs)
            except ValidationError as e:
                raise ValidationError({"store": e.messages_dict})
        elif widget_init:
            try:
                data["store"] = data["widget"].get_default_store(store_config, **field_kwargs)
            except ValidationError as e:
                raise ValidationError({"store": e.messages_dict})
        else:
            ctx = schema_context.get()
            field_name = ctx["field_name"]
            attr = ctx["entity"].get_model_attrs().get(field_name)
            if attr is not None:
                try:
                    store_class = BaseStore.get_store_from_attr(attr)
                except ValueError as e:
                    raise ValidationError(
                        {"store": f"{e}. Définissez explicitement un store et son type."}
                    )
                try:
                    data["store"] = store_class(store_config, **field_kwargs)
                except ValidationError as e:
                    raise ValidationError({"store": e.messages_dict})
            else:
                raise ValidationError("Vous devez fournir 'store' ou 'widget'")

        # At this point, the store exists.

        # Instanciation du widget à partir du store
        if not widget_init:
            try:
                data["widget"] = data["store"].get_default_widget(
                    data.get("widget"), **field_kwargs
                )
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

    @pre_dump
    def dump_widget_and_store(self, data, **kwarsg):
        return {
            **data,
            "widget": data["widget"].dump_config(),
            "store": data["store"].dump_config(),
        }

    @post_dump
    def retro_compat(self, data, **kwargs):
        # frontend requires type_widget & type_util, not widget & store :-(
        store = copy(data["store"])
        store["type_util"] = store.pop("type")
        widget = copy(data["widget"])
        widget["type_widget"] = widget.pop("type")
        if "hidden_js" in widget:
            widget["hidden"] = widget.pop("hidden_js")
        if "required_js" in widget:
            widget["required"] = widget.pop("required_js")
        data = {
            **data,
            **store,
            **widget,  # widget will override required with js condition if any
        }
        return data
