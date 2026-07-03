from sqlalchemy import (
    Integer,
    Float,
    String,
    Boolean,
    Date,
    ARRAY,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

TYPE_WIDGET = {
    "select": "varchar",
    "checkbox": "varchar",
    "radio": "varchar",
    "html": "text",
    "bool_checkbox": "boolean",
    "number": "integer",
    "multiselect": "varchar",
    "observers": "integer",
    "observers-text": "varchar",
    "media": "varchar",
    "medias": "varchar",
    "date": "date",
    "nomenclature": "integer",
    "datalist": "integer",
    "text": "varchar",
    "textarea": "text",
    "jsonb": "jsonb",
    "time": "varchar",
    "taxonomy": "integer",
    "site": "integer",
    "individuals": "integer",
    "dataset": "integer",
}

INT_TYPE_UTILS = [
    "user",
    "taxonomy",
    "nomenclature",
    "types_site",
    "module",
    "dataset",
    "site",
    "habitat",
]

OTHER_TYPE_UTILS = [
    "uuid",
    "date",
]

# Type de widget qui implique que multiple soit à true
MULTI_TYPE_WIDGET = ["multiselect", "checkbox"]

SQL_DATA_TYPE_MAPPING = {
    "varchar": String,
    "varchar[]": ARRAY(String),
    "text": Text,
    "boolean": Boolean,
    "integer": Integer,
    "integer[]": ARRAY(Integer),
    "number": Float(precision=24),
    "date": Date,
    "jsonb": JSONB,
    "uuid": UUID,
}

FORBIDDEN_SQL_INSTRUCTION = [
    "INSERT ",
    "DELETE ",
    "UPDATE ",
    "EXECUTE ",
    "TRUNCATE ",
    "ALTER ",
    "GRANT ",
    "COPY ",
    "PERFORM ",
    "CASCADE",
]

PERMISSION_LABEL = {
    "MONITORINGS_MODULES": {"label": "modules", "actions": ["R", "U", "E"]},
    "MONITORINGS_GRP_SITES": {"label": "groupes de sites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_SITES": {"label": "sites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_VISITES": {"label": "visites", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_INDIVIDUALS": {"label": "individus", "actions": ["C", "R", "U", "D"]},
    "MONITORINGS_MARKINGS": {"label": "marquages", "actions": ["C", "R", "U", "D"]},
}

ACTION_LABEL = {
    "C": "Créer des",
    "R": "Voir les",
    "U": "Modifier les",
    "D": "Supprimer des",
    "E": "Exporter les",
}

TABLE_NAME_SUBMODULE = {
    "sites_group": "t_sites_groups",
    "site": "t_base_sites",
    "visit": "t_base_visits",
    "observation": "t_observations",
    "observation_detail": "t_observations_details",
}

UUID_FIELD_NAME = {
    "sites_group": "uuid_sites_group",
    "site": "uuid_base_site",
    "visit": "uuid_base_visit",
    "observation": "uuid_observation",
    "observation_detail": "uuid_observation_detail",
}

TOOLTIPS = {
    "id_base_site_origin": "Identifiant alphanumérique permettant de faire le lien entre les sites et leurs visites si aucun UUID est fourni",
    "id_base_visit_origin": "Identifiant alphanumérique permettant de faire le lien entre les visites et leurs observations si aucun UUID est fourni",
}

ENTITIES_NOT_AVAILABLE = ["sites_group", "observation_detail"]
