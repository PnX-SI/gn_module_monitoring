"""
blueprint
charge les routes présentes dans le dossier route
"""

import json
import logging

import click
from flask import Blueprint, current_app, g, request
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from marshmallow import ValidationError

from geonature.utils.env import DB
from geonature.utils.config import config
from geonature.utils.json import register_json_provider
from geonature.core.admin.admin import admin as flask_admin
from geonature.core.gn_permissions.models import TObjects
from geonature.core.gn_commons.models.base import TModules

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.monitoring.admin import BibTypeSiteView
from gn_module_monitoring.command.cmd import commands  # noqa: E402
from gn_module_monitoring.command.utils import get_modules
from gn_module_monitoring.command.check.utils import get_object_types
from gn_module_monitoring.tools.adapters import BaseAdapter
from gn_module_monitoring.tools.widgets import BaseWidget
from gn_module_monitoring.config.module import load_module_config
from gn_module_monitoring.config.protocol import load_protocol_entity_config
from gn_module_monitoring.tools.utils import schema_context

log = logging.getLogger()

blueprint = Blueprint(
    "monitorings", __name__, template_folder=current_app.config["MEDIA_FOLDER"] + "/monitorings"
)


@blueprint.record_once
def register_serializer(state):
    register_json_provider(BaseAdapter, lambda o: o.dump_config())
    register_json_provider(BaseWidget, lambda o: o.dump_config())


@blueprint.record
def load_modues_config(state):
    monitoring_config = config[MODULE_CODE]
    monitoring_config["protocols"] = dict()
    for module in get_modules():
        module_code = module.module_code
        try:
            with schema_context(protocol_installed=True):
                protocol_config = load_module_config(module_code)
                for entity in get_object_types(protocol_config["tree"]):
                    protocol_config[entity] = load_protocol_entity_config(
                        module_code, entity=entity
                    )
                monitoring_config["protocols"][module_code] = protocol_config
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as e:
            ctx = click.get_current_context(silent=True)
            # Avoid printing errors when using the CLI
            if ctx is None:
                log.exception(e)
            log.warning(f"Unable to load protocol '{module_code}', skipping…")


@blueprint.teardown_request
def clear_current_module(exc=None):
    g.pop("current_module", None)
    g.pop("current_object", None)


@blueprint.before_request
def set_current_module():
    values = {**request.view_args, **request.args} if request.view_args else {**request.args}

    # recherche du sous-module courant
    requested_module_code = (
        values.get("module_code") or values.get("module_context") or MODULE_CODE
    )
    if requested_module_code == "generic":
        requested_module_code = "MONITORINGS"

    current_module = DB.first_or_404(
        statement=select(TModules)
        .options(joinedload(TModules.objects))
        .where(TModules.module_code == requested_module_code),
        description=f"No module with code {requested_module_code} ",
    )
    g.current_module = current_module

    # recherche de l'object de permission courant
    object_type = values.get("object_type")

    if object_type:
        permission_level = current_app.config["MONITORINGS"].get("PERMISSION_LEVEL", {})
        requested_permission_object_code = permission_level.get(object_type)

        if requested_permission_object_code is None:
            # error ?
            return

        # Test si l'object de permission existe
        requested_permission_object = DB.first_or_404(
            statement=select(TObjects).where(
                TObjects.code_object == requested_permission_object_code
            ),
            description=f"No permission object with code {requested_permission_object_code} ",
        )
        # si l'object de permission est associé au module => il devient l'objet courant
        # - sinon se sera 'ALL' par defaut
        for module_perm_object in current_module.objects:
            if module_perm_object == requested_permission_object:
                g.current_object = requested_permission_object
                return


import gn_module_monitoring.routes.config
import gn_module_monitoring.routes.data_utils
import gn_module_monitoring.routes.individuals
import gn_module_monitoring.routes.monitoring
import gn_module_monitoring.routes.modules
import gn_module_monitoring.routes.sites_groups
import gn_module_monitoring.routes.site
import gn_module_monitoring.routes.visit
import gn_module_monitoring.routes.observations
import gn_module_monitoring.routes.obs_detail

blueprint.cli.short_help = "Commandes pour l" "administration du module MONITORINGS"
for cmd in commands:
    blueprint.cli.add_command(cmd)

flask_admin.add_view(BibTypeSiteView(DB, name="Types de site", category="Monitorings"))
