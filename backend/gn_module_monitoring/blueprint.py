"""
    blueprint
    charge les routes présentes dans le dossier route
"""

from flask import Blueprint, current_app

from geonature.utils.env import DB
from geonature.core.admin.admin import admin as flask_admin

from gn_module_monitoring.monitoring.admin import BibTypeSiteView
from gn_module_monitoring.command.cmd import commands

blueprint = Blueprint(
    "monitorings", __name__, template_folder=current_app.config["MEDIA_FOLDER"] + "/monitorings"
)
from .routes import *  # noqa

blueprint.cli.short_help = "Commandes pour l" "administration du module MONITORINGS"
for cmd in commands:
    blueprint.cli.add_command(cmd)

flask_admin.add_view(BibTypeSiteView(DB.session, name="Types de site", category="Monitorings"))
