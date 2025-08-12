TYPE_WIDGET = {
    "select": "varchar",
    "checkbox": "varchar[]",
    "radio": "varchar",
    "html": "text",
    "bool_checkbox": "boolean",
    "number": "integer",
    "multiselect": "varchar[]",
    "observers": "integer[]",
    "media": "varchar",
    "medias": "varchar[]",
    "date": "date",
    "nomenclature": "integer",
    "datalist": "integer",
    "text": "varchar",
    "textarea": "text",
    "integer": "integer",
    "jsonb": "jsonb",
    "time": "varchar",
    "taxonomy": "integer",
    "site": "integer",
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
