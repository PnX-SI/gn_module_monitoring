"""
    blueprint
    charge les routes présentes dans le dossier route
"""

from flask import Blueprint, current_app

from .command.cmd_install import monitorings_cli

blueprint = Blueprint("monitorings", __name__)
from .routes import * # noqa

current_app.cli.add_command(monitorings_cli)
