"""
Géométrie des sites à l'import (monitoring), sans passer par les contrôles géométrie du cœur (ils ne sont plus appelés).

Chaîne :
1. `fill_wkt_from_xy` (après `check_types`) : si le WKT source est vide et que x et y sont
   renseignés et numériques, écrit `POINT(x y)` dans la colonne WKT source (SRID du fichier).
2. `check_wkt_geometries` : parse le WKT (`ImportGeometryField`), contrôle les bornes du SRID du
   fichier, et écrit la géométrie 4326 (`s__geom`) depuis le SRID du fichier. Un WKT invalide n'est
   pas signalé ici : il l'est par le schéma étendu (INVALID_WKT, voir `actions.py`).
3. `compute_geom_local` (SQL, post-check) : `geom_local` pour les lignes valides uniquement.
"""

import math

import pandas as pd
import sqlalchemy as sa
from geoalchemy2.functions import ST_GeomFromWKB, ST_Transform
from marshmallow import ValidationError, fields
from pyproj import CRS, Transformer
from shapely import wkt
from shapely.geometry import Polygon
from shapely.ops import transform
from utils_flask_sqla_geo.schema import GeometryField

from geonature.core.imports.checks.dataframe.utils import dataframe_check
from geonature.core.imports.checks.errors import ImportCodeError
from geonature.core.imports.models import BibFields, Entity, TImports
from geonature.core.imports.utils import get_mapping_data
from geonature.utils.env import db

from gn_module_monitoring.command.imports.constant import (
    TABLE_NAME_SUBMODULE,
    geom_local_column_name,
)
from gn_module_monitoring.tools.geometry import check_geometry_rules


class ImportGeometryField(GeometryField):
    """
    `GeometryField` dont le format est choisi par champ (`geometry_format`), et non par
    `schema.as_geojson`. Par défaut : WKT, sans SRID (le SRID du fichier est appliqué ensuite).

    La 3e dimension est rejetée en WKT comme en GeoJSON (ValidationError) : une seule règle à l'import.
    """

    def __init__(self, *args, geometry_format: str = "wkt", **kwargs):
        if geometry_format not in ("wkt", "geojson"):
            raise ValueError(f"Unknown geometry format: {geometry_format}")
        self.geometry_format = geometry_format
        super().__init__(*args, **kwargs)

    def _bind_to_schema(self, field_name, schema):
        # Ne pas reprendre le binding de GeometryField (il lit schema.as_geojson).
        fields.Field._bind_to_schema(self, field_name, schema)

    def _serialize(self, value, attr, obj, **kwargs):
        if self.geometry_format == "geojson":
            return self._serialize_geojson(value, attr, obj)
        return self._serialize_wkt(value, attr, obj)

    def _deserialize(self, value, attr, data, **kwargs):
        if self.geometry_format == "geojson":
            return self._deserialize_geojson(value, attr, data, **kwargs)
        try:
            geom = self._deserialize_wkt(value, attr, data, **kwargs)
        except ValidationError:
            raise
        except Exception as error:
            raise ValidationError("Invalid geometry.") from error
        # Règles communes à l'API (tools.geometry) : non vide, valide, sans 3e dimension.
        check_geometry_rules(geom)
        return geom


def get_srid_bounding_box(srid: int) -> Polygon:
    """Emprise (zone d'usage du CRS) du SRID, dans le SRID lui-même."""
    xmin, ymin, xmax, ymax = CRS.from_epsg(srid).area_of_use.bounds
    bounding_polygon_4326 = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
    projection = Transformer.from_crs(CRS(4326), CRS(int(srid)), always_xy=True)
    return transform(projection.transform, bounding_polygon_4326)


def _is_blank(value) -> bool:
    if isinstance(value, str):
        return value.strip() == ""
    return value is None or bool(pd.isna(value))


def _coordinate_to_float(value):
    """Nombre fini (virgule ou point décimal accepté), None sinon."""
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


@dataframe_check
def fill_wkt_from_xy(df: pd.DataFrame, wkt_field: BibFields, x_field: BibFields, y_field: BibFields):
    """
    Écrit `POINT(x y)` dans la colonne WKT source, pour les lignes où le WKT est vide et où x et y
    sont renseignés. x : longitude, y : latitude, dans le SRID du fichier.

    - x ou y non numérique : erreur INVALID_NUMERIC (la ligne devient invalide), pas de WKT ;
    - x ou y vide : pas de WKT (le contrôle des champs requis remonte l'erreur) ;
    - WKT existant : jamais écrasé. S'il est présent avec x et y, MULTIPLE_GEO_INFO_WARNING.
    """
    wkt_col = wkt_field.source_field
    x_col = x_field.source_field
    y_col = y_field.source_field
    if any(col not in df for col in (wkt_col, x_col, y_col)):
        return set()

    wkt_blank = df[wkt_col].map(_is_blank)
    x_blank = df[x_col].map(_is_blank)
    y_blank = df[y_col].map(_is_blank)

    for name, col, blank in (("s__x", x_col, x_blank), ("s__y", y_col, y_blank)):
        not_numeric = df[~blank][col].map(lambda v: _coordinate_to_float(v) is None)
        invalid_rows = df.loc[not_numeric[not_numeric].index]
        if len(invalid_rows):
            yield {
                "error_code": ImportCodeError.INVALID_NUMERIC,
                "column": name,
                "invalid_rows": invalid_rows,
            }

    both = ~x_blank & ~y_blank
    multiple = df[~wkt_blank & both]
    if len(multiple):
        yield {
            "error_code": ImportCodeError.MULTIPLE_GEO_INFO_WARNING,
            "column": "Champs géométriques",
            "invalid_rows": multiple,
        }

    xs = df[x_col].map(_coordinate_to_float)
    ys = df[y_col].map(_coordinate_to_float)
    to_fill = wkt_blank & xs.notna() & ys.notna()
    if not to_fill.any():
        return set()
    df[wkt_col] = df[wkt_col].astype(object)  # colonne entièrement vide lue en float
    df.loc[to_fill, wkt_col] = [
        f"POINT({x:.12f} {y:.12f})" for x, y in zip(xs[to_fill], ys[to_fill])
    ]
    return {wkt_col}


def fill_entity_wkt_from_xy(imprt: TImports, entity: Entity, df) -> set:
    """
    Écrit le WKT de l'entité depuis x et y (voir `fill_wkt_from_xy`), à partir de la configuration de
    l'entité du module : `geom_field_name`, `x` et `y` (noms d'import préfixés par l'entité).
    Ne fait rien si l'entité n'a pas de `geom_field_name`. Utilisable par toute entité géométrique.
    """
    from gn_module_monitoring.modules import get_module

    entity_fields, _, _ = get_mapping_data(imprt, entity)
    module_entity = get_module(imprt.destination.code).entities[entity.code]
    geom_field_name = module_entity.data.get("geom_field_name")
    if not geom_field_name:
        return set()
    return fill_wkt_from_xy(
        imprt,
        entity,
        df,
        wkt_field=entity_fields[module_entity.get_import_field_name(geom_field_name)],
        x_field=entity_fields[module_entity.get_import_field_name("x")],
        y_field=entity_fields[module_entity.get_import_field_name("y")],
    )


@dataframe_check
def check_wkt_geometries(
    df: pd.DataFrame,
    file_srid: int,
    wkt_field: BibFields,
    geom_4326_field: BibFields,
):
    """
    Parse le WKT source (SRID du fichier), contrôle les bornes de ce SRID et écrit la géométrie en
    SRID 4326 dans `geom_4326_field`. Les lignes au WKT invalide ou hors emprise n'ont pas de géométrie.

    Yields
    ------
    GEOMETRY_OUT_OF_BOX : géométrie hors de l'emprise du SRID du fichier.

    Notes
    -----
    Le WKT invalide n'est pas signalé ici : le schéma étendu le signale (INVALID_WKT).
    """
    wkt_col = wkt_field.source_field
    geom_col = geom_4326_field.dest_field
    if wkt_col not in df:
        return set()

    field = ImportGeometryField(geometry_format="wkt")
    filled = df[wkt_col].map(lambda v: not _is_blank(v))
    parsed = {}
    invalid = []
    for index, value in df.loc[filled, wkt_col].items():
        try:
            parsed[index] = field.deserialize(value)
        except ValidationError:
            invalid.append(index)

    bounding_box = get_srid_bounding_box(file_srid)
    out_of_box = [index for index, geom in parsed.items() if not geom.within(bounding_box)]
    if out_of_box:
        yield {
            "error_code": ImportCodeError.GEOMETRY_OUT_OF_BOX,
            "column": "WKT",
            "invalid_rows": df.loc[out_of_box],
        }
    for index in invalid + out_of_box:
        parsed.pop(index, None)

    if not parsed:
        return set()
    # Même principe que le cœur : expressions SQL écrites dans la colonne de la table transitoire.
    # La reprojection vers 4326 se fait en SQL, depuis le SRID du fichier.
    expressions = {}
    for index, geom in parsed.items():
        from_file = ST_GeomFromWKB(geom.wkb, file_srid)
        expressions[index] = from_file if file_srid == 4326 else ST_Transform(from_file, 4326)
    df[geom_col] = pd.Series(expressions, dtype=object).reindex(df.index)
    return {geom_col}


def get_geom_field_name(imprt: TImports, entity_code: str):
    """`geom_field_name` de l'entité du module de l'import (None si l'entité n'a pas de géométrie)."""
    from gn_module_monitoring.modules import get_module

    module_entity = get_module(imprt.destination.code).entities.get(entity_code)
    if module_entity is None:
        return None
    return module_entity.data.get("geom_field_name")


def compute_geom_local(
    imprt: TImports, entity: Entity, geom_4326_field: BibFields, geom_field_name: str
) -> None:
    """
    Calcule la géométrie locale de l'entité (colonne annexe, voir `geom_local_column_name`) depuis la
    géométrie 4326, pour les lignes valides uniquement. Le SRID local est lu dans la table de
    destination de l'entité.
    """
    geom_local_column = geom_local_column_name(geom_field_name)
    local_srid = db.session.scalar(
        sa.select(
            sa.func.Find_SRID("gn_monitoring", TABLE_NAME_SUBMODULE[entity.code], geom_local_column)
        )
    )
    transient_table = imprt.destination.get_transient_table()
    source_col = transient_table.c[geom_4326_field.dest_field]
    stmt = (
        sa.update(transient_table)
        .where(
            transient_table.c.id_import == imprt.id_import,
            transient_table.c[entity.validity_column] == True,
            source_col != None,
        )
        .values({geom_local_column: ST_Transform(source_col, local_srid)})
    )
    db.session.execute(stmt)
