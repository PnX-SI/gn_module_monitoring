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
from pyproj import CRS, Transformer
from shapely import wkb, wkt
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from gn_module_monitoring.tools.utils import schema_context


def parse_input_format(input_format: str) -> tuple[str, int]:
    """
    Décompose le format d'entrée : `geojson`, `wkt` ou `wkt;SRID=<code>` (ex. `wkt;SRID=2154`).
    Renvoie (`geojson` | `wkt`, SRID de la géométrie en entrée). GeoJSON est toujours en 4326 ;
    WKT sans SRID explicite : 4326.
    """
    if input_format == "geojson":
        return "geojson", 4326
    kind, _, srid = input_format.partition(";SRID=")
    if kind != "wkt" or (srid and not srid.isdigit()):
        raise ValueError(f"Format d'entrée géométrique inconnu : {input_format!r}")
    return "wkt", int(srid) if srid else 4326


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

    Si `store` est fourni, le type géométrique est validé contre `store.validate_geometry`, et le
    format d'entrée (GeoJSON par défaut, WKT si `store.get_input_format()` le demande) est lu dans le
    schéma contexte (voir `GeometryStore`).
    Sans `store` (géométrie native du modèle), le format d'entrée est lu de la même façon dans le
    schéma contexte (`geometry_format`, GeoJSON par défaut).
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
        if self.store is not None:
            input_format_name = self.store.get_input_format()
        else:
            input_format_name = (schema_context.get() or {}).get("geometry_format", "geojson")
        input_format, srid = parse_input_format(input_format_name)  # valide la valeur
        try:
            if input_format == "wkt":
                shape_ = wkt.loads(value)
                if srid != 4326:
                    shape_ = transform(
                        Transformer.from_crs(
                            CRS.from_epsg(srid), CRS.from_epsg(4326), always_xy=True
                        ).transform,
                        shape_,
                    )
            else:
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
