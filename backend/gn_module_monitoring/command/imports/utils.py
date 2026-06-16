import sqlalchemy as sa
from sqlalchemy import String
from geoalchemy2 import Geometry

from geonature.utils.env import db

from gn_module_monitoring.command.imports.constant import SQL_DATA_TYPE_MAPPING


def destination_name(module_name: str):
    return f"Monitoring - {module_name}"


def ask_confirmation(
    prompt="Veuillez confirmer que vous souhaitez effectuer avec ces modifications ? [yes/no]: ",
):

    response = input("\n" + prompt).strip().lower()

    while response not in ["yes", "y", "no", "n"]:
        print("Réponse invalide. Veuillez répondre par 'yes' ou 'no'.")
        response = input(prompt).strip().lower()

    return response in ["yes", "y"]


def map_field_type_sqlalchemy(type_column: str):
    """Map column types to SQLAlchemy column types"""
    srid_site = db.session.scalar(
        sa.select(sa.func.Find_SRID("gn_monitoring", "t_base_sites", "geom_local"))
    )

    type_mapping = SQL_DATA_TYPE_MAPPING | {
        "geometry_4326": Geometry("GEOMETRY", 4326),
        "geometry_local": Geometry("GEOMETRY", srid_site),
    }
    return type_mapping.get(type_column.lower(), String)
