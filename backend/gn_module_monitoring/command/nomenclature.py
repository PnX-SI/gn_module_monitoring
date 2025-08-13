from sqlalchemy import and_, select


from geonature.utils.env import DB
from geonature.core.gn_monitoring.models import BibTypeSite
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes


from gn_module_monitoring.config.utils import (
    json_from_file,
    monitoring_module_config_path,
)


def add_nomenclature(module_code):
    path_nomenclature = monitoring_module_config_path(module_code) / "nomenclature.json"

    if not path_nomenclature.is_file():
        print("Il n'y a pas de nomenclature à insérer pour ce module")
        return

    nomenclature = json_from_file(path_nomenclature, None)
    if not nomenclature:
        print("Il y a un problème avec le fichier {}".format(path_nomenclature))
        return

    for data in nomenclature.get("types", []):
        nomenclature_type = DB.session.execute(
            select(BibNomenclaturesTypes).where(
                data.get("mnemonique") == BibNomenclaturesTypes.mnemonique
            )
        ).scalar_one_or_none()

        if nomenclature_type:
            action = "already exist"
            print(
                "nomenclature type {} - {} - {}".format(
                    nomenclature_type.mnemonique, nomenclature_type.label_default, action
                )
            )

            continue

        data["label_fr"] = data.get("label_fr") or data["label_default"]
        data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
        data["source"] = data.get("source") or "monitoring"
        data["statut"] = data.get("statut") or "Validation en cours"

        nomenclature_type = BibNomenclaturesTypes(**data)
        DB.session.add(nomenclature_type)
        DB.session.commit()
        action = "added"
        print(
            "nomenclature type {} - {} - {}".format(
                nomenclature_type.mnemonique, nomenclature_type.label_default, action
            )
        )

    for data in nomenclature["nomenclatures"]:
        insert_update_nomenclature(data)


def insert_update_nomenclature(data):

    # Get Id type
    id_type = DB.session.execute(
        select(BibNomenclaturesTypes.id_type).where(
            BibNomenclaturesTypes.mnemonique == data["type"]
        )
    ).scalar_one_or_none()

    if not id_type:
        print(
            'probleme de type avec mnemonique="{}" pour la nomenclature {}'.format(
                data["type"], data
            )
        )
        return

    # Get nomenclature if exist
    action = "updated"
    nomenclature = DB.session.execute(
        select(TNomenclatures)
        .join(BibNomenclaturesTypes, BibNomenclaturesTypes.id_type == TNomenclatures.id_type)
        .where(
            and_(
                data.get("cd_nomenclature") == TNomenclatures.cd_nomenclature,
                data.get("type") == BibNomenclaturesTypes.mnemonique,
            )
        )
    ).scalar_one_or_none()

    # If not create new one
    if not nomenclature:
        nomenclature = TNomenclatures()
        action = "added"

    data["label_fr"] = data.get("label_fr") or data["label_default"]
    data["definition_fr"] = data.get("definition_fr") or data["definition_default"]
    data["source"] = data.get("source") or "monitoring"
    data["statut"] = data.get("statut") or "Validation en cours"
    data["active"] = True
    data["id_type"] = id_type

    for key, value in data.items():
        if hasattr(nomenclature, key):
            setattr(nomenclature, key, value)

    DB.session.add(nomenclature)
    DB.session.commit()
    if data["type"] == "TYPE_SITE":
        existing_bib_type_site = DB.session.get(BibTypeSite, nomenclature.id_nomenclature)
        if not existing_bib_type_site:
            bib_type_site = BibTypeSite(id_nomenclature_type_site=nomenclature.id_nomenclature)
            DB.session.add(bib_type_site)
            DB.session.commit()

    print(
        "nomenclature {} - {} - {}".format(
            nomenclature.cd_nomenclature, nomenclature.label_default, action
        )
    )
