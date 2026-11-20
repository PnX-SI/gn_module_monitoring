"""
Géométrie échangée avec l’API : un seul champ, utilisé par le schéma des sites / groupes de sites
et par le store de géométrie (`GeometryStore`).

Règles communes à l’API et à l’import (voir `check_geometry_rules`) : géométrie non vide, valide,
sans 3e dimension.
"""

import json

from geoalchemy2.shape import from_shape, to_shape
from geojson import Feature
from marshmallow import ValidationError, fields
from shapely import wkb
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry


def check_geometry_rules(geom: BaseGeometry) -> None:
    """
    Règles de validation d’une géométrie, identiques pour l’API et l’import.

    Raises
    ------
    ValidationError : géométrie vide, invalide, ou avec une 3e dimension.
    """
    if geom.is_empty:
        raise ValidationError("Empty geometry.")
    if not geom.is_valid:
        raise ValidationError("Invalid geometry.")
    if geom.has_z:
        raise ValidationError("Unexpected third dimension.")


class GeojsonSerializationField(fields.Field):
    """
    Géométrie échangée avec l’API en GeoJSON (sortie : dict GeoJSON ; entrée : dict GeoJSON ou
    chaîne JSON), en SRID 4326. Entrée acceptée aussi : géométrie Shapely ou WKB.
    La 3e dimension est rejetée (voir `check_geometry_rules`).

    Si `store` est fourni, le type géométrique est validé contre `store.validate_geometry`.
    """

    def __init__(self, store=None, **kwargs):
        super().__init__(**kwargs)
        self.store = store

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return value
        if type(value).__name__ == "WKBElement":
            return Feature(geometry=to_shape(value)).geometry
        return None

    def _deserialize(self, value, attr, data, **kwargs):
        if not value:
            return None
        try:
            if isinstance(value, str):
                value = json.loads(value)
            if isinstance(value, BaseGeometry):
                shape_ = value
            elif isinstance(value, (bytes, bytearray)):
                shape_ = wkb.loads(bytes(value))
            elif type(value).__name__ == "WKBElement":
                shape_ = to_shape(value)
            else:
                shape_ = shape(value)
        except Exception as error:
            raise ValidationError("Geometry error") from error
        check_geometry_rules(shape_)
        if self.store is not None:
            self.store.validate_geometry(shape_)
        return from_shape(shape_, srid=4326)
