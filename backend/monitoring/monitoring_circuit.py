from sqlalchemy import text

from ..repositories.config import (
    config_param
)

from .monitoring_object import get_object_id_parent

from geonature.utils.env import DB

RADIUS_OF_BUFFER_CIRCUIT = 0.1


def is_circuit_points(module_path, object_type):
    return config_param(module_path, object_type, 'circuit_type') == 'points'


def is_parent_circuit_points(module_path, object_type):
    parent_type = config_param(module_path, object_type, 'parent_type')
    return is_circuit_points(parent_type)


def fake_circuit_points_geom():
    # islande
    return {
        'type': 'Polygon',
        'coordinates': [[
                [-16.11831665039063, 65.65871673504769],
                [-16.11874580383301, 65.65693013922441],
                [-16.121449470520023, 65.658239142283]
        ]]
    }


def request_circuit_b_geom_modified(id_circuit, b_geom_modified):
    str_geom_modified = 'true' if b_geom_modified else 'false'
    return """
UPDATE gn_monitoring.t_base_sites
    SET data = ('{{"b_geom_modified":' || {1} || '}}')::jsonb
        WHERE NOT EXISTS (SELECT 1 FROM JSONB_EACH(data) s)
            AND id_base_site = {0};

UPDATE gn_monitoring.t_base_sites
    SET data = data ||'{{}}'::jsonb || ('{{"b_geom_modified":' || {1} || '}}' )::jsonb
        WHERE id_base_site = {0};
        """.format(
                    id_circuit,
                    str_geom_modified
                )


def request_circuit_geom(id_circuit, radius_of_buffer):
    # !! on rajoute 1e-3 a radius sinon bug quand radius = 0 (1 seul point écoute)
    return """
UPDATE gn_monitoring.t_base_sites SET (geom) = (
    SELECT ST_BUFFER(geom, (radius + 1e-3)*{1}) FROM
        ( SELECT geom, (SELECT radius FROM ST_MinimumBoundingRadius(geom))
            FROM
                ( SELECT ST_ConvexHull(ST_Collect(geom)) as geom
                        FROM gn_monitoring.t_base_sites
                        WHERE data->>'id_parent' = '{0}'
                )a
        )b
)
    WHERE id_base_site = {0}
        AND (data->>'b_geom_modified')::boolean
;
            """.format(id_circuit, radius_of_buffer)


def check_and_set_parent_circuit_b_geom_modified(module_path, object_type, id_object, b_geom_modified):

    parent_type = config_param(module_path, object_type, 'parent_type')
    if not is_circuit_points(module_path, parent_type):
        return

    id_circuit = get_object_id_parent(module_path, object_type, id_object)

    if not id_circuit:
        return

    return set_circuit_b_geom_modified(module_path, parent_type, id_circuit, b_geom_modified)


def set_circuit_b_geom_modified(module_path, object_type, id_circuit, b_geom_modified):

    if not (is_circuit_points(module_path, object_type) and id_circuit):
        return

    DB.engine.execute(
        text(
            request_circuit_b_geom_modified(id_circuit, b_geom_modified)
        )
    )


def check_and_set_circuit_points_geom(module_path, object_type, id_circuit):

    if not (is_circuit_points(module_path, object_type) and id_circuit):
        return

    DB.engine.execute(
        text(
            request_circuit_geom(id_circuit, RADIUS_OF_BUFFER_CIRCUIT)
        )
    )

    set_circuit_b_geom_modified(module_path, object_type, id_circuit, False)
