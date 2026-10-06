import click
import sqlalchemy as sa

from geonature.utils.env import db

from pypnnomenclature.models import TNomenclatures

from gn_module_monitoring.command.check.nomenclature import get_nomenclature, get_nomenclature_type
from gn_module_monitoring.command.check.utils import (
    CheckResult,
    wrap_errors,
)
from gn_module_monitoring.command.imports.constant import MULTI_TYPE_WIDGET


def is_multiple(field_conf: dict) -> bool:
    multiple = field_conf.get("multiple", field_conf.get("multi_select", False))
    if isinstance(multiple, str):
        multiple = multiple.strip().lower() in ["true", "vrai", "oui", "yes", "1"]
    return bool(multiple) or field_conf.get("type_widget") in MULTI_TYPE_WIDGET


def get_object_types(config: dict):
    """
    Retourne la liste des objets du protocole (sites, visites, observations...)
    pour lesquels des données spécifiques sont stockées, en parcourant
    l'arbre des objets défini dans la configuration.
    """

    def iter_tree(tree):
        for object_type, children in (tree or {}).items():
            yield object_type
            if children is not None:
                yield from iter_tree(children)

    object_types = ["module"]
    for object_type in iter_tree(config.get("tree")):
        if object_type not in object_types:
            object_types.append(object_type)

    return object_types


def get_fields_config(config: dict, object_type: str):
    """
    Retourne la configuration des champs d'un objet, la configuration
    spécifique prenant le pas sur la configuration générique.
    """
    object_config = config.get(object_type)
    if not isinstance(object_config, dict):
        return {}

    fields = {}
    for scope in ["generic", "specific"]:
        scope_fields = object_config.get(scope)
        if isinstance(scope_fields, dict):
            fields.update(
                {
                    field_name: field_conf
                    for field_name, field_conf in scope_fields.items()
                    if isinstance(field_conf, dict)
                }
            )
    return fields


def get_table(name, schema="gn_monitoring"):
    return db.metadata.tables["{}.{}".format(schema, name)]


OBJECTS_TABLE_NAME = {
    "module": ("t_module_complements", "id_module"),
    "sites_group": ("t_sites_groups", "id_sites_group"),
    "site": ("t_site_complements", "id_base_site"),
    "visit": ("t_visit_complements", "id_base_visit"),
    "observation": ("t_observation_complements", "id_observation"),
    "observation_detail": ("t_observation_details", "id_observation_detail"),
}


def get_data_rows(object_type: str, id_module: int, row_ids=None):
    """
    Retourne la liste des couples (identifiant, données) des objets d'un
    protocole.

    Si `row_ids` est renseigné, seuls ces enregistrements sont retournés.
    """

    complements_table_name, id_column_name = OBJECTS_TABLE_NAME[object_type]
    complements = get_table(complements_table_name)
    id_column = complements.c[id_column_name]

    if object_type == "module":
        query = sa.select(id_column, complements.c.data).where(id_column == id_module)
    elif object_type == "sites_group":
        module_link = get_table("cor_sites_group_module")
        query = (
            sa.select(id_column, complements.c.data)
            .join(
                module_link,
                module_link.c.id_sites_group == id_column,
            )
            .where(module_link.c.id_module == id_module)
        )
    elif object_type == "site":
        module_link = get_table("cor_site_module")
        query = (
            sa.select(id_column, complements.c.data)
            .join(module_link, module_link.c.id_base_site == id_column)
            .where(module_link.c.id_module == id_module)
        )
    elif object_type == "visit":
        visits = get_table("t_base_visits")
        query = (
            sa.select(id_column, complements.c.data)
            .join(visits, visits.c.id_base_visit == id_column)
            .where(visits.c.id_module == id_module)
        )
    elif object_type == "observation":
        observations = get_table("t_observations")
        visits = get_table("t_base_visits")
        query = (
            sa.select(id_column, complements.c.data)
            .join(observations, observations.c.id_observation == id_column)
            .join(visits, visits.c.id_base_visit == observations.c.id_base_visit)
            .where(visits.c.id_module == id_module)
        )
    elif object_type == "observation_detail":
        observations = get_table("t_observations")
        visits = get_table("t_base_visits")
        query = (
            sa.select(id_column, complements.c.data)
            .join(observations, observations.c.id_observation == complements.c.id_observation)
            .join(visits, visits.c.id_base_visit == observations.c.id_base_visit)
            .where(visits.c.id_module == id_module)
        )
    else:
        raise Exception(f"Unexpected object type '{object_type}'")

    if row_ids:
        query = query.where(id_column.in_(row_ids))

    return [(id_row, data) for id_row, data in db.session.execute(query)]


def update_row(object_type, row_id, data):
    complements_table_name, id_column_name = OBJECTS_TABLE_NAME[object_type]
    complements = get_table(complements_table_name)
    id_column = complements.c[id_column_name]

    db.session.execute(sa.update(complements).where(id_column == row_id).values(data=data))
    db.session.commit()

    yield "\n" + click.style(f"Enregistrement {row_id} mis à jour", fg="green")


def check_nomenclature_value(row_id, field_name, field_conf, value, fix):
    updated_value = None

    mnemonique = field_conf.get("code_nomenclature_type")
    if mnemonique is None:
        yield f"Missing mnemonique in field '{field_name}' config"
        return
    nomenclature_type = get_nomenclature_type(mnemonique)
    if nomenclature_type is None:
        yield f"Nomenclature type not found for mnemonique '{mnemonique}'"
        return

    if type(value) != int:
        yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - valeur '{value}' : pas un entier"
        if type(value) == str:
            nomenclature = get_nomenclature(
                nomenclature_type, TNomenclatures.cd_nomenclature.ilike(value)
            )
            if nomenclature is not None:
                yield f"\nLa nomenclature {nomenclature.id_nomenclature} a été trouvée par cd_nomenclature"
            else:
                nomenclature = get_nomenclature(
                    nomenclature_type, TNomenclatures.mnemonique.ilike(value)
                )
                if nomenclature is not None:
                    yield f"\nLa nomenclature '{nomenclature.id_nomenclature}' a été trouvée par mnemonique"
            if nomenclature is not None:
                yield f"\n  mnemonique: {nomenclature.mnemonique}"
                yield f"\n  cd_nomenclature: {nomenclature.cd_nomenclature}"
                yield f"\n  label_default: {nomenclature.label_default}"
                yield f"\n  label_fr: {nomenclature.label_fr}"
                yield f"\n  definition_default: {nomenclature.definition_default}"
                yield f"\n  definition_fr: {nomenclature.definition_fr}"
                if fix and click.confirm("Utiliser ?"):
                    updated_value = nomenclature.id_nomenclature
                else:
                    return
        else:
            return
    else:
        nomenclature = get_nomenclature(nomenclature_type, id_nomenclature=value)
        if nomenclature is None:
            yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - valeur '{value}' : non trouvée"
            return

    if nomenclature is None:
        return

    cd_nomenclatures = field_conf.get("cd_nomenclatures")
    if cd_nomenclatures and nomenclature.cd_nomenclature not in cd_nomenclatures:
        yield f"[id={row_id}] Type de nomenclature '{nomenclature_type}' - cd_nomenclature '{nomenclature.cd_nomenclature}' : non autorisée"
        yield "\nValeurs admises :"
        for cd_nomenclature in cd_nomenclatures:
            yield f"\n  {cd_nomenclature}"

    return updated_value


def check_datalist_value(field_conf, value):
    # TODO: check allowed values…
    pass


def check_field(row_id, field_name: str, field_conf: dict, value, fix):
    """
    Vérifie la valeur d'un champ par rapport à sa configuration.
    """
    # TODO: check required value
    if value is None:
        return
    updated_value = None
    if not is_multiple(field_conf) and type(value) is list and len(value) == 1:
        yield f"[{row_id}] {field_name} : champs non-multi mais une liste de longueur 1 a été trouvée"
        if fix and click.confirm("Applatir ?"):
            updated_value = value[0]
            value = updated_value
    if field_conf.get("type_util") == "nomenclature":
        updated_value = yield from check_nomenclature_value(
            row_id, field_name, field_conf, value, fix
        )
        value = updated_value

    return updated_value
    # TODO: other types…


def check_row(row_id, config, data):
    """
    Contrôle la cohérence globale des données de l’objet.
    """
    # TODO: implement jsonschema here
    return
    yield


def check_module_data_type(config, fix, data_filters, id_module, object_type):
    if any(data_filters.values()) and not (
        data_filters.get(object_type)
        or data_filters.get(f"{object_type}_pks")
        or data_filters.get(f"{object_type}_fields")
    ):
        return CheckResult("[SKIP]", bold=True)

    fields_config = get_fields_config(config, object_type)
    rows = get_data_rows(object_type, id_module, data_filters.get(f"{object_type}_pks"))
    if not rows:
        return CheckResult("[NO DATA]", bold=True)

    fields_to_check = data_filters.get(f"{object_type}_fields") or None

    for row_id, data in rows:
        if data is None:
            continue

        if not isinstance(data, dict):
            yield f"[{row_id}] Les données ne sont pas un dictionnaires ({type(data)}"
            continue

        modified_row = False
        for field_name, value in data.items():
            if fields_to_check and field_name not in fields_to_check:
                continue
            field_config = fields_config.get(field_name)
            if field_config is None:
                yield f"[{row_id}] Le champs '{field_name}'' n’est pas défini dans la configuration du protocole"
                continue

            updated_value = yield from check_field(row_id, field_name, field_config, value, fix)
            if updated_value is not None:
                data[field_name] = updated_value
                modified_row = True
        if modified_row:
            yield from update_row(object_type, row_id, data)

        yield from check_row(row_id, config, data)


def check_module_data(config: dict, fix: bool, data_filters: None | dict = None):
    total_error_count = 0
    id_module = config["module"]["id_module"]
    for object_type in get_object_types(config):
        error_count, _ = wrap_errors(
            f"Données - {object_type}",
            check_module_data_type(config, fix, data_filters, id_module, object_type),
        )
        total_error_count += error_count
    return total_error_count
