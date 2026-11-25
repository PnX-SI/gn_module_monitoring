"""
Base commune des classes d'actions d'import des entités (`SiteImportActions`, `VisitImportActions`, ...).
"""

from typing import ClassVar


class BaseImportActions:
    # Préfixe des noms d'import des champs de l'entité (`s__`, `v__`, ...)
    FIELD_PREFIX: ClassVar[str | None] = None
    # Champ identifiant de l'entité (gardé sans préfixe à l'import)
    ID_FIELD: ClassVar[str | None] = None

    @classmethod
    def get_field_name(cls, field_name: str) -> str:
        """
        Nom d'import (`name_field` de bib_fields, `s__kind`, `v__meteo`, `uuid_base_site`, ...) du champ
        `field_name` de la configuration de l'entité.

        - l'identifiant de l'entité (`ID_FIELD`), les UUID (`uuid_*`) et les identifiants d'origine
          (`*_origin`) gardent leur nom nu ;
        - les autres champs sont préfixés par `FIELD_PREFIX` (`s__`, `v__`, ...).
        Cette règle ne consulte pas IGNORED_IMPORT_FIELDS : un champ exclu de l'import est filtré
        par l'appelant (`build_field_names`).
        """
        if field_name == cls.ID_FIELD:
            return field_name
        if field_name.startswith("uuid_") or field_name.endswith("_origin"):
            return field_name
        return f"{cls.FIELD_PREFIX}{field_name}"
