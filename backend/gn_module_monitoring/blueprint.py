"""
    blueprint
    charge les routes présentes dans le dossier route
"""

from flask import Blueprint, current_app
from geonature.core.admin.admin import admin as flask_admin
from geonature.utils.env import DB

from gn_module_monitoring.monitoring.admin import BibTypeSiteView
from .command.cmd import commands

blueprint = Blueprint("monitorings", __name__)
from .routes import *  # noqa

blueprint.cli.short_help = "Commandes pour l" "administration du module MONITORINGS"
for cmd in commands:
    blueprint.cli.add_command(cmd)

flask_admin.add_view(BibTypeSiteView(DB.session, name="Types de site", category="Monitorings"))
