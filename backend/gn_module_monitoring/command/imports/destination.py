from sqlalchemy import select, exists
import sqlalchemy as sa


from geonature.utils.env import db
from geonature.core.gn_commons.models import TModules
from geonature.core.imports.models import (
    Destination,
)


def upsert_bib_destination(module_data: dict) -> Destination:
    """
    Ajoute ou met à jour une destination dans bib_destinations.

    Parameters
    ----------
    module_data : dict
        Données de la table gn_commons.t_modules du module à importer.

    Returns
    -------
    Destination
        L'objet Destination inséré ou mis à jour (SQLAlchemy model)
    """
    dest_exists = db.session.execute(
        exists().where(Destination.code == module_data["module_code"]).select()
    ).scalar()

    if dest_exists:
        existing_destination = db.session.execute(
            select(Destination).filter_by(code=module_data["module_code"])
        ).scalar_one()

        data = {
            "label": module_data["module_label"],
            "table_name": f"t_imports_{module_data['module_code'].lower()}",
            "module_code": module_data["module_code"],
        }
        for key, value in data.items():
            setattr(existing_destination, key, value)
        db.session.flush()
        return existing_destination

    module_monitoring_code = db.session.execute(
        select(TModules).filter_by(module_code=module_data["module_code"])
    ).scalar_one()
    destination_data = {
        "id_module": module_monitoring_code.id_module,
        "code": module_data["module_code"],
        "label": module_data["module_label"],
        "table_name": f"t_imports_{module_data['module_code'].lower()}",
    }
    destination = Destination(**destination_data)
    db.session.add(destination)
    db.session.flush()
    return destination
