"""
blueprint
charge les routes présentes dans le dossier route
"""

from flask import Blueprint, current_app, g, request
from urllib.parse import urlparse, parse_qs

from geonature.utils.env import DB
from geonature.core.admin.admin import admin as flask_admin

from gn_module_monitoring import MODULE_CODE
from gn_module_monitoring.monitoring.admin import BibTypeSiteView
from gn_module_monitoring.command.cmd import commands  # noqa: E402
from geonature.core.gn_permissions.models import TObjects
from geonature.core.gn_commons.models.base import TModules
from sqlalchemy.orm import joinedload
from sqlalchemy import select

blueprint = Blueprint(
    "monitorings", __name__, template_folder=current_app.config["MEDIA_FOLDER"] + "/monitorings"
)


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


from .routes import *  # noqa

blueprint.cli.short_help = "Commandes pour l" "administration du module MONITORINGS"
for cmd in commands:
    blueprint.cli.add_command(cmd)

flask_admin.add_view(BibTypeSiteView(DB.session, name="Types de site", category="Monitorings"))
