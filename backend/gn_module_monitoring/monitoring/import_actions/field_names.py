"""
Correspondance entre deux familles de noms de champs :
- l'*import field name* : `name_field` d'un champ de `bib_fields` (`s__kind`, `v__meteo`, ...).
  Les colonnes de la table transitoire et du DataFrame en découlent via `source_column`
  (`src_<import field name>`, valeur brute) et `dest_column` (`<import field name>`, valeur
  typée) : ce ne sont pas des import field names ;
- l'*entity field name* : nom du champ dans la configuration du protocole (clé de
  `entity.data["fields"]`, `kind`, `meteo`, ...).

Le backend lit ces données sur l'entité chargée (`get_module(code).entities[nom].data`).

Règle de construction : `BaseImportActions.get_field_name` (monitoring/import_actions/base.py), qui
reprend la règle de `prepare_fields` et `monitoring_field_to_bib_field` (command/imports/fields.py).
"""

from dataclasses import dataclass, field

from gn_module_monitoring.command.imports.constant import IGNORED_IMPORT_FIELDS
from gn_module_monitoring.tools.utils import cel_entity_variables

CEL_FIELD_PREFIX = "fields."


@dataclass
class FieldNames:
    entity_code: str
    # import field name -> entity field name
    import_to_entity: dict[str, str] = field(default_factory=dict)
    # entity field name -> raison pour laquelle le champ n'est pas importé
    ignored_entity_fields: dict[str, str] = field(default_factory=dict)
    # variables CEL (`fields.<entity field name>`) qui ne désignent pas un champ importé -> raison
    ignored_cel_variables: dict[str, str] = field(default_factory=dict)

    @property
    def entity_to_import(self) -> dict[str, str]:
        """entity field name -> import field name"""
        return {entity: imported for imported, entity in self.import_to_entity.items()}

    def import_field_name_of(self, entity_field_name: str) -> str | None:
        return self.entity_to_import.get(entity_field_name)


def build_field_names(entity_code: str, entity) -> FieldNames:
    """
    Construit les correspondances de noms de champs d'une entité chargée (objet avec `.data`).

    Les variables CEL sont celles de `cel_entity_variables` : toute variable qui ne désigne pas
    un champ importé est signalée (D-IC9).
    """
    names = FieldNames(entity_code=entity_code)
    fields = entity.data["fields"]

    for entity_field_name in fields:
        # Une entité sans actions d'import (ex. `module`) n'a aucun champ importable
        import_field_name = (
            None
            if entity_field_name in IGNORED_IMPORT_FIELDS or entity.import_actions_class is None
            else entity.import_actions_class.get_field_name(entity_field_name)
        )
        if import_field_name is None:
            names.ignored_entity_fields[entity_field_name] = (
                "champ ignoré à l'import (IGNORED_IMPORT_FIELDS)"
            )
        else:
            names.import_to_entity[import_field_name] = entity_field_name

    for variable in cel_entity_variables(entity):
        entity_field_name = variable.removeprefix(CEL_FIELD_PREFIX)
        if entity_field_name not in fields:
            names.ignored_cel_variables[variable] = "champ absent de la configuration"
        elif entity_field_name in names.ignored_entity_fields:
            names.ignored_cel_variables[variable] = names.ignored_entity_fields[entity_field_name]

    return names
