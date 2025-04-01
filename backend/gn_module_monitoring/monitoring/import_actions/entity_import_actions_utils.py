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
    def generate_id(
        imprt: TImports, entity: Entity, table_name: str, uuid_field_name: str, id_field_name: str
    ) -> None:
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

        transient_table = imprt.destination.get_transient_table()
        uuid_valid_cte = (
            sa.select(
                sa.distinct(transient_table.c[uuid_field_name]).label(uuid_field_name),
                sa.func.min(transient_table.c.line_no).label("line_no"),
            )
            .where(transient_table.c.id_import == imprt.id_import)
            .where(transient_table.c[entity.validity_column].is_(True))
            .group_by(transient_table.c[uuid_field_name])
            .cte("uuid_valid_cte")
        )

        db.session.execute(
            sa.update(transient_table)
            .where(transient_table.c.line_no == uuid_valid_cte.c.line_no)
            .values(
                {
                    f"{id_field_name}": sa.func.nextval(
                        f"gn_monitoring.{table_name}_{id_field_name}_seq"
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

    @staticmethod
    def get_destination_fields(imprt: TImports, entity: Entity) -> None:
        fields = {
            ef.field.name_field: ef.field for ef in entity.fields if ef.field.dest_field != None
        }
        entity_fields = set()
        # insert_fields = {fields["id_station"]}
        for field_name, mapping in imprt.fieldmapping.items():
            if field_name not in fields:  # not a destination field
                continue
            field = fields[field_name]
            column_src = mapping.get("column_src", None)
            if field.multi:
                if not set(column_src).isdisjoint(imprt.columns):
                    entity_fields |= {field}
            else:
                if column_src in imprt.columns or mapping.get("default_value", None) is not None:
                    entity_fields |= {field}

        if entity.code == "site":
            entity_fields |= {
                fields["id_base_site"],
                fields["s__geom_4326"],
                fields["s__geom_local"],
            }
            entity_fields -= {fields["s__types_site"]}
        elif entity.code == "visit":
            entity_fields |= {
                fields["id_base_site"],
                fields["id_base_visit"],
                fields["id_dataset"],
            }
        elif entity.code == "observation":
            # We don't select id_observation because it must be generated by the DB on insert
            entity_fields |= {
                fields["id_base_visit"],
            }

        return entity_fields
