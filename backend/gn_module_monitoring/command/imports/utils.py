from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import (
    Integer,
    String,
    Boolean,
    Date,
    ARRAY,
    Text,
)
import sqlalchemy as sa
from geoalchemy2 import Geometry

from geonature.utils.env import db


def ask_confirmation():
    prompt = (
        "\nVeuillez confirmer que vous souhaitez effectuer avec ces modifications ? [yes/no]: "
    )

    response = input(prompt).strip().lower()

    while response not in ["yes", "y", "no", "n"]:
        print("Réponse invalide. Veuillez répondre par 'yes' ou 'no'.")
        response = input(prompt).strip().lower()

    return response in ["yes", "y"]


def map_field_type_sqlalchemy(type_widget: str):
    """Map widget types to SQLAlchemy column types"""
    srid_site = db.session.scalar(
        sa.select(sa.func.Find_SRID("gn_monitoring", "t_base_sites", "geom_local"))
    )
    type_mapping = {
        "varchar": String,
        "varchar[]": ARRAY(String),
        "text": Text,
        "boolean": Boolean,
        "integer": Integer,
        "integer[]": ARRAY(Integer),
        "date": Date,
        "jsonb": JSONB,
        "uuid": UUID,
        "geometry_4326": Geometry("GEOMETRY", 4326),
        "geometry_local": Geometry("GEOMETRY", srid_site),
    }
    return type_mapping.get(type_widget.lower(), String)
