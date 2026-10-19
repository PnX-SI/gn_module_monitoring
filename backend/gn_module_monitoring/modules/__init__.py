from collections import UserDict
from copy import deepcopy
import json

import sqlalchemy as sa
from flask import current_app

from geonature.utils.env import db
from pypnusershub.db.models import UserList

from gn_module_monitoring import EXTENSION_CODE
from gn_module_monitoring.tools.utils import schema_context
from gn_module_monitoring.config.utils import monitoring_module_config_path
from gn_module_monitoring.config.module import ModuleConfigSchema
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.config.utils import (
    get_monitorings_path,
    is_module_configured,
)
from gn_module_monitoring.tools.stores import NomenclatureStore
from gn_module_monitoring.modules.entities import ENTITY_MAP


def get_substitutions(module):
    substitutions = {
        f"__MODULE.{attr.upper()}": getattr(module, attr)
        for attr in [
            "module_code",
            "id_list_taxonomy",
            "id_list_observer",
            "b_synthese",
            "b_draw_sites_group",
            "taxonomy_display_field_name",
            "id_module",
            "cd_nom",
        ]
    }
    if module.id_list_observer:
        substitutions["__MODULE.CODE_OBSERVERS_LIST"] = db.session.execute(
            sa.select(UserList.code_liste).where(UserList.id_liste == module.id_list_observer)
        ).scalar_one()
    else:
        substitutions["__MODULE.CODE_OBSERVERS_LIST"] = current_app.config["MONITORINGS"][
            "CODE_OBSERVERS_LIST"
        ]
    substitutions["__MONITORINGS_PATH"] = get_monitorings_path()
    substitutions["__MODULE.IDS_TYPE_SITE"] = [
        {"id_nomenclature_type_site": t.id_nomenclature_type_site} for t in module.types_site
    ]
    return substitutions


def get_tree_entities(tree: dict):
    """
    Retourne la liste des objets du sous-module (sites, visites, observations...)
    pour lesquels des données spécifiques sont stockées, en parcourant
    l'arbre des objets défini dans la configuration.
    """

    def iter_tree(tree):
        for object_type, children in (tree or {}).items():
            yield object_type
            if children is not None:
                yield from iter_tree(children)

    object_types = ["module"]
    for object_type in iter_tree(tree):
        if object_type not in object_types:
            object_types.append(object_type)

    return object_types


class MonitoringModule(UserDict):
    @property
    def config_path(self):
        return monitoring_module_config_path(self.module_code) / "config.json"

    @property
    def entities_list(self):
        return get_tree_entities(self["tree"])

    def __init__(self, module_code):
        self.module_code = module_code
        if module_code == "generic":
            config = {}
        else:
            config = json.loads(self.config_path.read_text())
        self.config_schema = ModuleConfigSchema()
        with schema_context(module=self):
            super().__init__(self.config_schema.load(config))
        if module_code == "generic":
            self.module = None
            self["configured"] = True
            self.substitutions = {}
        else:
            self.module = db.session.execute(
                sa.select(TMonitoringModules).where(TMonitoringModules.module_code == module_code)
            ).scalar_one()
            self["configured"] = is_module_configured(self.module)
            self.substitutions = get_substitutions(self.module)

        self.entities = {}
        for entity in self.entities_list:
            self.entities[entity] = ENTITY_MAP[entity](self)

    def collect_nomenclatures(self):
        """
        Retourne les types de nomenclature (mnémonique) à précharger côté frontend,
        à partir des stores de nomenclature de tous les champs des entités.
        """
        types = ["TYPE_MEDIA"]  # FIXME: retro-compat?
        for entity in self.entities.values():
            for field in entity.data["fields"].values():
                store = field["store"]
                if isinstance(store, NomenclatureStore) and store["nomenclature_type"] is not None:
                    types.append(store["nomenclature_type"].mnemonique)
        return list(dict.fromkeys(types))

    def dump_config(self):
        """
        Retourne la config telle qu’attendue par le frontend.
        """

        module_config = self.config_schema.dump(self)
        for entity in self.entities:
            module_config[entity] = self.entities[entity].dump_config()

        module_config["custom"] = self.substitutions

        module_config.setdefault("data", {})["nomenclature"] = self.collect_nomenclatures()

        return module_config


def get_module(module_code):
    if module_code not in current_app.extensions[EXTENSION_CODE]["modules"]:
        current_app.extensions[EXTENSION_CODE]["modules"][module_code] = MonitoringModule(
            module_code
        )
    return current_app.extensions[EXTENSION_CODE]["modules"][module_code]
