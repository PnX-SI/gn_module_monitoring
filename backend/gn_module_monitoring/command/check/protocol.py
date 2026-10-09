from copy import deepcopy
import json
import importlib
from typing import Any

import marshmallow as ma
from marshmallow import fields, pre_load, post_load, validates_schema, ValidationError

from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.command.utils import validate_json_file_protocol
from gn_module_monitoring.command.check.utils import MultilineStr, wrap_errors, get_object_types
from gn_module_monitoring.command.check.widgets import (
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
    ObserversWidget,
    ObserversTextWidget,
)
from gn_module_monitoring.command.check.adapters import (
    StringAdapter,
    UserAdapter,
    ObserverListAdapter,
    NomenclatureAdapter,
    TaxonomyAdapter,
    TaxonomyListAdapter,
    DatasetAdapter,
    HabitatAdapter,
    TypesSiteAdapter,
    ModuleAdapter,
    UUIDAdapter,
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
        ObserversWidget.key: ObserversWidget,
        ObserversTextWidget.key: ObserversTextWidget,
        DatasetWidget.key: DatasetWidget,
        HabitatWidget.key: HabitatWidget,
        MediaWidget.key: MediaWidget,
        ObserversTextWidget.key: ObserversTextWidget,
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
        ObserverListAdapter.key: ObserverListAdapter,
        NomenclatureAdapter.key: NomenclatureAdapter,
        TaxonomyAdapter.key: TaxonomyAdapter,
        TaxonomyListAdapter.key: TaxonomyListAdapter,
        DatasetAdapter.key: DatasetAdapter,
        HabitatAdapter.key: HabitatAdapter,
        TypesSiteAdapter.key: TypesSiteAdapter,
        ModuleAdapter.key: ModuleAdapter,
        UUIDAdapter.key: UUIDAdapter,
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
        unknown = ma.INCLUDE  # TODO: switch to raise once schema complete

    name = fields.Str(required=True)
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
        # retro-compat.
        if "type_widget" in data:
            # TODO: gérer le mélange type_widget + widget due à générique + spécifique
            data["widget"] = deepcopy(data)
            data["widget"]["type"] = data.pop("type_widget")
        if "type_util" in data:
            # TODO: gérer le mélange type_util + adapter due à générique + spécifique
            data["adapter"] = deepcopy(data)
            data["adapter"]["type"] = data.pop("type_util")
        return data

    @post_load(pass_original=True)
    def post_load(self, data, original_data, **kwargs):
        # Instanciation de l’adapter à partir du widget
        if "widget" in data and "adapter" not in data:
            try:
                data["adapter"] = data["widget"].get_default_adapter()
            except ValidationError as e:
                raise ValidationError({"adapter": e.messages_dict})
        # Instanciation du widget à partir de l’adapter
        if "adapter" in data and "widget" not in data:
            try:
                data["widget"] = data["adapter"].get_default_widget()
            except ValidationError as e:
                raise ValidationError({"widget": e.messages_dict})
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

    fields = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Nested(FieldProtocolSchema))
    # fields = ma.fields.List(ma.fields.Nested(FieldProtocolSchema))
    display_list = ma.fields.List(ma.fields.Str(), load_default=[])
    display_properties = ma.fields.List(ma.fields.Str(), load_default=[])

    @pre_load
    def pre_load(self, data, **kwargs):
        """
        Ce hook s’occupe de merger la config generic avec la config specific.
        """
        # retro.compat
        if "specific" in data:
            data["fields"] = data.pop("specific")
        # Permet de valider de manière minimale les fields pour les manipuler
        fields_field = fields.Dict(keys=fields.Str(), values=fields.Dict())
        data["fields"] = fields_field.deserialize(data.get("fields", {}))
        # TODO: plutôt que charger la config par défaut depuis un fichier par défaut, la mettre directement
        # dans les schémas afin de centraliser les infos de la config.
        default_data = json.loads(
            importlib.resources.read_text(
                "gn_module_monitoring.config.generic", f"{self.entity}.json"
            )
        )
        # retro-compat.
        if "generic" in default_data:
            default_data["fields"] = default_data.pop("generic")
        default_data["fields"] = fields_field.deserialize(default_data.get("fields", {}))
        # On écrase tous les champs, sauf "fields"
        # TODO: veut-on vraiment permettre de tous écraser ???
        full_data = {**default_data, **{k: v for k, v in data.items() if k != "fields"}}
        # Maintenant, pour les fields, on permet :
        #   - de définir de nouveau fields
        #   - d’override, pour les fields existant dans default_data, uniquement :
        #     - le widget
        #     - required, seulement si c’est pour le forcer à True
        for field_name, field_def in data["fields"].items():
            if field_name in default_data["fields"]:  # field existant
                # TODO: Comportement legacy, adopter le comportement strict décrit ci-dessus
                full_data["fields"][field_name].update(field_def)
            else:  # nouveau field, on l’ajoute
                full_data["fields"][field_name] = field_def
        # On transforme le dict de fields en list, pour que chaque field est connaissance de sa clé
        full_data["fields"] = {k: {**v, "name": k} for k, v in full_data["fields"].items()}
        return full_data

    @validates_schema
    def validates_schema(self, data, **kwargs):
        for field in data["display_list"]:
            if field not in data["fields"]:
                raise ValidationError({"display_list": f"Le champs '{field}' n’a pas été défini."})
        for field in data["display_properties"]:
            if field not in data["fields"]:
                raise ValidationError(
                    {"display_properties": f"Le champs '{field}' n’a pas été défini."}
                )


class ModuleProtocolSchema(BaseProtocolSchema):
    entity = "module"


class SitesGroupProtocolSchema(BaseProtocolSchema):
    entity = "sites_group"


class SiteProtocolSchema(BaseProtocolSchema):
    # TODO: si sites_group fait partie du tree, alors site a par défaut un champs id_sites_group d’ajouté
    # voir SITES_GROUP_CONFIG et process_schema dans config/utils.py
    entity = "site"


class VisitProtocolSchema(BaseProtocolSchema):
    entity = "visit"


class ObservationProtocolSchema(BaseProtocolSchema):
    entity = "observation"


class ObservationDetailProtocolSchema(BaseProtocolSchema):
    entity = "observation"


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
        raise NotImplementedError

    config_path = monitoring_module_config_path(module_code) / f"{entity}.json"
    if config_path.is_file():
        try:
            with config_path.open() as f:
                entity_config = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            yield e
            return
    else:
        entity_config = {}

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
        # TODO: remplacer les templates (__MONITORINGS_PATH, etc.)
        error_count, config[entity] = wrap_errors(
            f"Définition du protocole - {entity}",
            check_module_protocol_entity(module_code, entity),
            return_result=True,
        )
        total_error_count += error_count

    return total_error_count
