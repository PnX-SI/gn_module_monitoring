"""
Fonctions utilisées par les routes de l'ancienne API (breadcrumbs, suppression, synthèse, export pdf)
encore appelées par l'interface.

Elles reposent sur la configuration renvoyée par `get_config` (champs dans config[object_type]["fields"])
et remplacent les méthodes équivalentes de MonitoringObject, qui reste basé sur `get_config_old`.
"""

import json
import logging

from flask import g
from sqlalchemy import select, text
from werkzeug.exceptions import NotFound

from geonature.core.gn_synthese.utils.process import import_from_table
from geonature.utils.env import DB

from gn_module_monitoring.monitoring.definitions import MonitoringModels_dict
from gn_module_monitoring.monitoring.models import TMonitoringModules
from gn_module_monitoring.monitoring.schemas import add_specific_attributes
from gn_module_monitoring.monitoring.serializer import MonitoringSerializer_dict

log = logging.getLogger(__name__)


def get_object_model(module_code, object_type, id, config):
    """
    Renvoie l'objet SQLAlchemy correspondant à `id`.
    Pour un module, l'objet est récupéré à partir de `module_code` si `id` n'est pas défini.
    Lève une erreur 404 si l'objet n'existe pas.
    """
    Model = MonitoringModels_dict[object_type]
    if object_type == "module" and not id:
        condition = Model.module_code == module_code
    else:
        condition = getattr(Model, config[object_type]["id_field_name"]) == id

    model = DB.session.execute(select(Model).where(condition)).unique().scalar_one_or_none()
    if model is None:
        raise NotFound(f"{object_type} {id or module_code} not found")
    return model


def get_field_value(model, field_name):
    """Valeur d'un champ, qu'il soit une colonne du modèle ou une propriété spécifique (data)"""
    if hasattr(model, field_name):
        return getattr(model, field_name)
    return (getattr(model, "data", None) or {}).get(field_name)


def get_id_parent(module_code, object_type, model, config):
    parent_types = config[object_type].get("parent_types") or []
    if not parent_types:
        return None
    if "module" in parent_types[0]:
        return module_code
    return getattr(model, config[parent_types[0]]["id_field_name"], None)


def _module_breadcrumb():
    module_code = g.current_module.module_code
    return {
        "description": g.current_module.module_label,
        "id": g.current_module.id_module,
        "label": "Module",
        "module_code": "generic" if module_code.upper() == "MONITORINGS" else module_code,
        "object_type": "module",
    }


def get_breadcrumbs(module_code, object_type, id, config, params):
    """
    Renvoie la liste des breadcrumbs de l'objet et de ses parents (du plus haut au plus bas).

    Si `params["parents_path"]` est renseigné, les parents sont pris dans cette liste (en partant de la fin),
    sinon on remonte le premier type de parent défini dans la configuration.
    """
    model = get_object_model(module_code, object_type, id, config) if id else None

    breadcrumbs = []
    if model is not None:
        object_config = config[object_type]
        breadcrumb = {
            "id": getattr(model, object_config["id_field_name"]),
            "label": object_config.get("label"),
            "description": str(get_field_value(model, object_config["description_field_name"])),
            "module_code": "generic" if module_code.upper() == "MONITORINGS" else module_code,
            "object_type": object_type,
        }
        if params["parents_path"]:
            breadcrumb["params"] = {"parents_path": list(params["parents_path"])}
        breadcrumbs.append(breadcrumb)

    if params["parents_path"]:
        parent_type = params["parents_path"].pop()
        if parent_type == "module":
            return [_module_breadcrumb()] + breadcrumbs
        parent_id_field_name = config[parent_type]["id_field_name"]
        parent_id = (
            model is not None and get_field_value(model, parent_id_field_name)
        ) or params.get(parent_id_field_name)
    else:
        parent_types = config[object_type].get("parent_types") or []
        parent_type = parent_types[0] if parent_types else None
        if not parent_type or parent_type == "module":
            return breadcrumbs
        parent_id = get_id_parent(module_code, object_type, model, config) if model else None

    return get_breadcrumbs(module_code, parent_type, parent_id, config, params) + breadcrumbs


def process_synthese(module_code, config, limit=1000):
    """
    Synchronise la synthèse avec la vue gn_monitoring.v_synthese_<module_code> pour tout le module.
    Renvoie True si la synchronisation a été faite.
    """
    if not config.get("synthese"):
        return

    module = get_object_model(module_code, "module", None, config)
    id_field_name = config["module"]["id_field_name"]
    table_name = f"v_synthese_{module_code.lower()}"

    # Test de l'existence de la colonne de synchronisation sur la vue synthese
    column_exist = DB.session.execute(
        text("""
            SELECT count(*)
            FROM information_schema.columns
            WHERE   table_schema=:table_schema
                AND table_name=:table_name
                AND column_name=:column_name;
            """),
        params={
            "table_schema": "gn_monitoring",
            "table_name": table_name,
            "column_name": id_field_name,
        },
    ).scalar_one()

    if column_exist == 0:
        log.error(
            f"Monitoring - Synchronisation synthèse : Column {id_field_name} does not exist on view {table_name}"
        )
        return

    import_from_table(
        "gn_monitoring", table_name, id_field_name, getattr(module, id_field_name), limit
    )
    return True


def serialize_object(module_code, object_type, model, config):
    """
    Sérialise un objet (propriétés génériques et spécifiques à plat + géométrie)
    au format utilisé par les templates d'export pdf :
    {"properties": {...}, "geometry": {...}, "object_type": ..., "module_code": ..., "id": ...}
    """
    schema = add_specific_attributes(
        MonitoringSerializer_dict[object_type], object_type, module_code
    )
    properties = schema().dump(model)
    properties["id_parent"] = get_id_parent(module_code, object_type, model, config)

    # Libellés des types de site (et leurs ids dans ids_types_site)
    if properties.get("types_site") and hasattr(model, "types_site"):
        properties["types_site"] = [t.nomenclature.label_fr for t in model.types_site]
        properties["ids_types_site"] = [t.id_nomenclature_type_site for t in model.types_site]

    geom_geojson = getattr(model, "geom_geojson", None)
    return {
        "properties": properties,
        "geometry": json.loads(geom_geojson) if geom_geojson else None,
        "object_type": object_type,
        "module_code": module_code,
        "id": getattr(model, config[object_type]["id_field_name"]),
    }
