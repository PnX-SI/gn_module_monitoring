INT_TYPE_UTILS = [
    "user",
    "taxonomy",
    "nomenclature",
    "types_site",
    "module",
    "dataset",
    "site",
    "habitat",
    "sites_group",
    "area",
]

OTHER_TYPE_UTILS = [
    "uuid",
    "date",
]

# Type de widget qui implique que multiple soit à true
MULTI_TYPE_WIDGET = ["multiselect", "checkbox", "municipalities", "areas"]

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
    "INDIVIDUALS": {"label": "individus", "actions": ["C", "R", "U", "D"]},
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

# Champs de configuration non importés dans bib_fields (gérés à part, générés ou dynamiques).
# TODO: définir une liste par entités plutôt qu’une liste globale
IGNORED_IMPORT_FIELDS = [
    "id_module",  # handled manually
    "id_digitiser",  # handled manually
    "uuid_base_visit",  # handled manually
    "uuid_base_site",  # handled manually
    "uuid_observation",  # handled manually
    "id_base_site",  # generated
    "id_base_visit",  # generated
    "id_observation",  # generated
    "id_nomenclature_type_site",  # handled manually
    "last_visit",  # dynamic
    "nb_visits",  # dynamic
    "nb_observations",  # dynamic
    "nb_individuals",  # dynamic
    "nb_marking_events",  # dynamic
    "medias",  # not importable
    "id_sites_group",  # ignored for now
]



def geom_local_column_name(geom_field_name: str) -> str:
    """
    Colonne annexe de la géométrie locale d'une entité, dérivée de son champ géométrie
    (`geom_field_name` de l'entité, ex. `geom` -> `geom_local`). Ce n'est ni un champ import only ni un
    bib_fields : la colonne est ajoutée à la table transitoire (command/imports/sql.py), calculée en SQL
    après contrôle (monitoring/import_actions/geometry.py), puis transférée vers la table de l'entité
    (monitoring/import_actions/actions.py).
    """
    return f"{geom_field_name}_local"


def entity_import_field_name(entity_code: str, field_name: str) -> str:
    """
    Nom d'import d'un champ import only (identifiant d'origine, UUID, x, y, JDD), préfixé comme les
    autres champs de l'entité (`ENTITY_MAP[entity_code].get_import_field_name`). L'identifiant de
    l'entité (id_base_site, ...) garde son nom nu.
    """
    from gn_module_monitoring.modules.entities import ENTITY_MAP

    return ENTITY_MAP[entity_code].get_import_field_name(field_name)


# TODO: propriété sur les entités ?
TOOLTIPS = {
    "id_base_site_origin": "Identifiant alphanumérique permettant de faire le lien entre les sites et leurs visites si aucun UUID est fourni",
    "id_base_visit_origin": "Identifiant alphanumérique permettant de faire le lien entre les visites et leurs observations si aucun UUID est fourni",
}

# Entités de l'arbre du module qui ne sont pas importées (pas de destination d'import) :
# groupes de sites, détail d'observation, individus et marquages (suivi CMR).
# TODO: à faire, sites_group initié dans https://github.com/PnX-SI/gn_module_monitoring/pull/593 avant le refact
ENTITIES_NOT_AVAILABLE = ["sites_group", "observation_detail", "individual", "marking"]

# Valeur pouvant être retourné suite à l'analyse de la modification du protocole
# cas de la mise à jour d'un module


class ValidationFlag:
    """
    Enumération des flags de validation.
    """

    LABEL = "LABEL"
    FIELDS = "FIELDS"
    NOTHING = "NOTHING"
    INVALID = "INVALID"
