from geonature.core.imports.models import Entity, TImports
from geonature.core.imports.checks.dataframe.cast import check_types
from geonature.core.imports.checks.dataframe.core import check_required_values

from geonature.utils.env import db
import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload

from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
)

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
)


class EntityImportActionsUtils:
    @staticmethod
    def get_entity(imprt: TImports, entity_code: str) -> Entity:
        return Entity.query.filter_by(
            code=entity_code, id_destination=imprt.destination.id_destination
        ).one()

    @staticmethod
    def dataframe_checks(imprt, df, entity, fields):
        updated_cols = set({})
        updated_cols |= check_types(
            imprt, entity, df, fields
        )  # FIXME do not check site and visit uuid twice

        updated_cols |= check_required_values(imprt, entity, df, fields)

        return updated_cols

    # TODO ? Use explicit params instead of doing string interpolations.

    @staticmethod
    def generate_id(imprt: TImports, entity: Entity) -> None:
        """
        Generate the id for each new valid entity

        Parameters
        ----------
        imprt : TImports
            _description_
        entity : Entity
            entity
        """
        # Generate an id for the first occurence of each UUID
        field_name = f"uuid_base_{entity.code}"
        transient_table = imprt.destination.get_transient_table()
        uuid_valid_cte = (
            sa.select(
                sa.distinct(transient_table.c[field_name]).label(field_name),
                sa.func.min(transient_table.c.line_no).label("line_no"),
            )
            .where(transient_table.c.id_import == imprt.id_import)
            .where(transient_table.c[entity.validity_column].is_(True))
            .group_by(transient_table.c[field_name])
            .cte("uuid_valid_cte")
        )

        db.session.execute(
            sa.update(transient_table)
            .where(transient_table.c.line_no == uuid_valid_cte.c.line_no)
            .values(
                {
                    f"id_base_{entity.code}": sa.func.nextval(
                        f"gn_monitoring.t_base_{entity.code}s_id_base_{entity.code}_seq"
                    )
                }
            )
        )

    @staticmethod
    def set_parent_id_from_line_no(imprt: TImports, entity: Entity) -> None:
        """
        Set the parent id of each entity in the transient table using the line_no of the corresponding parent.

        Parameters
        ----------
        imprt : TImports
            The import object containing the destination.
        entity : Entity
            entity
        """
        transient_entity = imprt.destination.get_transient_table()
        transient_parent = aliased(transient_entity)
        parent_code = entity.parent.code
        db.session.execute(
            sa.update(transient_entity)
            .where(
                transient_entity.c.id_import == imprt.id_import,
                transient_entity.c[entity.validity_column].is_(True),
                transient_parent.c.id_import == imprt.id_import,
                transient_parent.c.line_no == transient_entity.c[f"{parent_code}_line_no"],
            )
            .values({f"id_base_{parent_code}": transient_parent.c[f"id_base_{parent_code}"]})
        )
