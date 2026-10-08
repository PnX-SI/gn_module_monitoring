import json
import importlib
from typing import Any

import marshmallow as ma
from marshmallow import fields, pre_load, post_load, ValidationError

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.command.utils import validate_json_file_protocol
from gn_module_monitoring.command.check.utils import MultilineStr, wrap_errors, get_object_types
from gn_module_monitoring.command.check.widgets import (
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
    MediaWidget,
)
from gn_module_monitoring.command.check.adapters import (
    StringAdapter,
    UserAdapter,
    NomenclatureAdapter,
    TaxonomyAdapter,
)


class WidgetProtocolSchema(ma.Schema):
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
        MediaWidget.key: MediaWidget,
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


class AdapterProtocolSchema(ma.Schema):
    adapter_map = {
        UserAdapter.key: UserAdapter,
        NomenclatureAdapter.key: NomenclatureAdapter,
        TaxonomyAdapter.key: TaxonomyAdapter,
    }

    type = fields.Str(required=True)

    def load(self, data, **kwargs):
        data = super().load(data, unknown=ma.INCLUDE)
        if data["type"] in self.adapter_map:
            adapter = self.adapter_map[data["type"]]
            return adapter(data, **kwargs)
        else:
            raise ValidationError(
                {
                    "type": f"Type d’apdapter '{data["type"]}' inconnu. Types autorisés : {', '.join(self.adapter_map)}"
                }
            )


class FieldProtocolSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE

    # FIXME: actuellement, on peut spécifier que le widget (resp. l’adapter) auquel cas l’adapter (resp. le widget) est déterminé automatiquement.
    # Comment utiliser, pour un widget donnée, l’adapter par défaut, mais overrider certaines propriétés ?
    widget = fields.Nested(WidgetProtocolSchema)
    adapter = fields.Nested(AdapterProtocolSchema)

    required = fields.Boolean(load_default=False)
    required_js = MultilineStr()
    hidden = fields.Boolean(load_default=False)
    hidden_js = MultilineStr()

    @pre_load
    def pre_load(self, data, **kwargs):
        # Si required (resp. hidden) n’est pas un booléen, c’est une valeur dynamique à évaluer en js.
        # On considère le champs commen non requis (resp. non masqué) en l’absence de possibilité de savoir ce qu’il en est réellement.
        if "required" in data and not isinstance(data["required"], bool):
            data["required_js"] = data.pop("required")
            data["required"] = False
        if "hidden" in data and not isinstance(data["hidden"], bool):
            data["hidden_js"] = data.pop("hidden")
            data["hidden"] = False
        return data

    @post_load(pass_original=True)
    def post_load(self, data, original_data, **kwargs):
        # retro-compat.: load widget & adapter with full original data, ignoring extra keys
        if "widget" not in data and "type_widget" in original_data:
            try:
                data["widget"] = WidgetProtocolSchema().load(
                    {"type": original_data.pop("type_widget"), **original_data},
                    unknown=ma.EXCLUDE,
                )
            except ValidationError as e:
                raise ValidationError({"widget": e.messages_dict})
        if "adapter" not in data and "type_util" in original_data:
            try:
                data["adapter"] = AdapterProtocolSchema().load(
                    {"type": original_data.pop("type_util"), **original_data},
                    unknown=ma.EXCLUDE,
                )
            except ValidationError as e:
                raise ValidationError({"adapter": e.messages_dict})

        if "widget" in data and "adapter" not in data:
            try:
                data["adapter"] = data["widget"].get_default_adapter(
                    original_data,
                    unknown=ma.EXCLUDE,
                )
            except ValidationError as e:
                raise ValidationError({"adapter": e.messages_dict})
        if "adapter" in data and "widget" not in data:
            data["widget"] = data["adapter"].get_default_widget(
                original_data,
                unknown=ma.EXCLUDE,
            )
        elif "widget" not in data and "adapter" not in data:
            data["widget"] = TextWidget()
            data["adapter"] = StringAdapter()

        # Vérification de la cohérence des données entre le widget et l’adapter.
        # Si l’un des deux renvoit None, cela veut dire que le type n’est pas connue
        # (typiquement datalist qui ne connait pas le type de retour de l’API)
        # et dans ce cas la vérification ne peut pas avoir lieu.
        widget_wire_type = data["widget"].get_wire_type()
        adapter_wire_type = data["adapter"].get_wire_type()
        if (
            widget_wire_type != adapter_wire_type
            and widget_wire_type is not Any
            and adapter_wire_type is not Any
        ):
            raise ValidationError(
                f"Incohérence de type : {data["widget"]} renvoit '{widget_wire_type}' alors que {data["adapter"]} attend '{adapter_wire_type}'"
            )

        return data


class BaseProtocolSchema(ma.Schema):
    class Meta:
        # TODO: le but est de passer à RAISE une fois les schémas complets
        unknown = ma.EXCLUDE

    fields = fields.Dict(keys=fields.Str(), values=fields.Nested(FieldProtocolSchema))

    @pre_load
    def specific(self, data, **kwargs):
        # retro compat.
        if "specific" in data:
            data["fields"] = data.pop("specific")
        return data


class ModuleProtocolSchema(BaseProtocolSchema):
    pass


class SitesGroupProtocolSchema(BaseProtocolSchema):
    pass


class SiteProtocolSchema(BaseProtocolSchema):
    pass


class VisitProtocolSchema(BaseProtocolSchema):
    pass


class ObservationProtocolSchema(BaseProtocolSchema):
    pass


class ObservationDetailProtocolSchema(BaseProtocolSchema):
    pass


def check_module_protocol_entity(module_code, entity):
    # TODO: intégration directement dans les schémas des valeurs par défaut actuellement dans les fichiers génériques ?

    if entity == "module":
        schema = ModuleProtocolSchema()
    elif entity == "sites_group":
        schema = SitesGroupProtocolSchema()
    elif entity == "site":
        schema = SiteProtocolSchema()
    elif entity == "visit":
        schema = VisitProtocolSchema()
    elif entity == "observation":
        schema = ObservationProtocolSchema()
    elif entity == "observation_detail":
        schema = ObservationDetailProtocolSchema()
    # TODO: individual, marking
    else:
        raise Exception(f"Unexpected entity '{entity}'")

    config_path = monitoring_module_config_path(module_code) / f"{entity}.json"
    if not config_path.is_file():
        return
    try:
        with config_path.open() as f:
            entity_config = json.load(f)
    except (json.JsonDecodeError, UnicodeDecodeError) as e:
        yield e
        return

    default_config = json.loads(
        importlib.resources.read_text("gn_module_monitoring.config.generic", f"{entity}.json")
    )

    # entity_config = deep

    try:
        entity_config = schema.load(entity_config)
    except ma.exceptions.ValidationError as e:
        yield e.messages

    return entity_config


def legacy_check(module_code):
    # Legacy checks
    _is_valid, errors = validate_json_file_protocol(module_code)
    yield from errors


def check_module_protocol(module_code, config):
    """
    Contrôle la validité des fichiers de definition du protocole.
    """

    total_error_count = wrap_errors("Définition du protocole", legacy_check(module_code))

    for entity in get_object_types(config["tree"]):
        error_count, config[entity] = wrap_errors(
            f"Définition du protocole - {entity}",
            check_module_protocol_entity(module_code, entity),
            return_result=True,
        )
        total_error_count += error_count

    return total_error_count
