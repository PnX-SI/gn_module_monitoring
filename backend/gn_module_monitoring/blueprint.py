"""
    blueprint
    charge les routes présentes dans le dossier route
"""

from flask import Blueprint, current_app
from .command.cmd import commands

blueprint = Blueprint("monitorings", __name__)
from .routes import *  # noqa

blueprint.cli.short_help = "Commandes pour l" "administration du module MONITORINGS"
for cmd in commands:
    blueprint.cli.add_command(cmd)
