"""
    blueprint
    charge les routes présentes dans le dossier route
"""

from flask import Blueprint

blueprint = Blueprint("monitorings", __name__)

from .routes import * # noqa
