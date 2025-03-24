from math import ceil
import re
from geonature.core.imports.checks.dataframe.cast import check_types
from geonature.core.imports.checks.dataframe.core import check_datasets, check_required_values
from geonature.core.imports.checks.dataframe.geometry import check_geometry
from geonature.core.imports.checks.sql.extra import check_entity_data_consistency
from geonature.core.imports.checks.sql.parent import set_parent_line_no
import sqlalchemy as sa
from sqlalchemy.orm import aliased, joinedload

from geonature.core.imports.actions import ImportActions
from geonature.core.imports.checks.sql.core import check_orphan_rows, init_rows_validity
from geonature.core.imports.models import Entity, TImports
from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
)

from geonature.utils.env import db

from bokeh.embed.standalone import StandaloneEmbedJson
from flask import current_app

import typing


class ImportStatisticsLabels(typing.TypedDict):
    key: str
    value: str

# TODO factorize with same function in command/utils.py
def get_field_name(entity_code, field_name):
    if entity_code == "sites_group":
        return f"g__{field_name}"
    elif entity_code == "observation_detail":
        return f"d__{field_name}"
    return f"{entity_code[0]}__{field_name}"


def get_entities(imprt: TImports) -> typing.Tuple[Entity, Entity, Entity]:
    entity_site = Entity.query.filter_by(code="site").one()
    entity_visit = Entity.query.filter_by(code="visit").one()
    entity_observation = Entity.query.filter_by(
        code="observation", id_destination=imprt.destination.id_destination
    ).one()
    return entity_site, entity_visit, entity_observation


# TODO ? Use explicit params instead of doing string interpolations.
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
    field_name = get_field_name(entity.code, f"uuid_base_{entity.code}")
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


def check_entity_sql(imprt, entity: Entity):
    _, parent_fields, _ = get_mapping_data(imprt, entity.parent)
    _, entity_fields, _ = get_mapping_data(imprt, entity)
    parent_code = entity.parent.code
    set_parent_line_no(
        imprt,
        parent_entity=entity.parent,
        child_entity=entity,
        id_parent=f"id_base_{parent_code}",
        parent_line_no=f"{parent_code}_line_no",
        fields=[
            entity_fields.get(f"id_base_{parent_code}"),
            parent_fields.get(f"s__uuid_base_{parent_code}"),
        ],
    )


""" def check_visit_sql(imprt):
    entity_site, entity_visit, _ = get_entities(imprt)
    _, site_fields, _ = get_mapping_data(imprt, entity_site)
    _, visit_fields, _ = get_mapping_data(imprt, entity_visit)
    
    set_parent_line_no(
        imprt,
        parent_entity=entity_site,
        child_entity=entity_visit,
        id_parent="id_base_site",
        parent_line_no="site_line_no",
        fields=[
            visit_fields.get("id_base_site"),
            site_fields.get("s__uuid_base_site"),
        ],
    )


def check_observation_sql(imprt):
    _, entity_visit, entity_observation = get_entities(imprt)
    _, visit_fields, _ = get_mapping_data(imprt, entity_visit)
    _, observation_fields, _ = get_mapping_data(imprt, entity_observation)
    
    set_parent_line_no(
        imprt,
        parent_entity=entity_visit,
        child_entity=entity_observation,
        id_parent="id_base_visit",
        parent_line_no="visit_line_no",
        fields=[
            observation_fields.get("id_base_visit"),
            visit_fields.get("v__uuid_base_visit"),
        ],
    ) """


class MonitoringImportActions(ImportActions):
    @staticmethod
    def statistics_labels() -> typing.List[ImportStatisticsLabels]:
        return []

    # Some field params appears to be dynamic
    # They must be handled on the fly
    # Ex. process
    # {
    #   "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
    #   ...
    # }
    # TO
    # "api": "users/menu/2",
    @staticmethod
    def process_fields(destination, entities):
        from gn_module_monitoring.config.repositories import get_config

        config = get_config(destination.code)
        customs = config["custom"]
        for entity in entities:
            for theme in entity["themes"]:
                for field in theme["fields"]:
                    type_field_params = field["type_field_params"]
                    if isinstance(type_field_params, dict):
                        for k, v in type_field_params.items():
                            if isinstance(v, str):
                                for c_k, c_v in customs.items():
                                    if isinstance(c_v, (str, int, float)) and c_k in v:
                                        v = v.replace(c_k, str(c_v))
                                field["type_field_params"][k] = v

        return entities

    # The output of this method is NEVER used
    @staticmethod
    def preprocess_transient_data(imprt: TImports, df) -> set:
        pass

    @staticmethod
    def check_transient_data(task, logger, imprt: TImports) -> None:
        from gn_module_monitoring.config.repositories import get_config

        config = get_config(imprt.destination.code)

        task.update_state(state="PROGRESS", meta={"progress": 0})
        init_rows_validity(imprt)
        task.update_state(state="PROGRESS", meta={"progress": 0.05})
        check_orphan_rows(imprt)
        task.update_state(state="PROGRESS", meta={"progress": 0.1})

        # We first check site and visit consistency in order to avoid checking
        # incoherent data
        MonitoringImportActions.check_parents_consistency(imprt)

        # We run dataframes checks before SQL checks in order to avoid
        # check_types overriding generated values during SQL checks.
        MonitoringImportActions.check_site_dataframe(imprt, config)
        MonitoringImportActions.check_visit_dataframe(imprt)
        MonitoringImportActions.check_observation_dataframe(imprt)

        _, entity_visit, entity_observation = get_entities(imprt)

        check_entity_sql(imprt, entity_visit)
        check_entity_sql(imprt, entity_observation)

    def import_data_to_destination(imprt: TImports) -> None:
        transient_table = imprt.destination.get_transient_table()
        entities = {
            entity.code: entity
            for entity in (
                db.session.scalars(
                    sa.select(Entity)
                    .where(Entity.destination == imprt.destination)
                    .options(joinedload(Entity.fields))
                    .order_by(Entity.order)
                )
                .unique()
                .all()
            )
        }

        def get_dest_col_name(input: str) -> str:
            return re.sub(r"^.*?__", "", input)

        for entity in entities.values():
            print(f"--------- {entity.code}")
            if entity.code in ["site", "visit"]:
                """
                !!! Almost same comment as OcchabImportActions.import_data_to_destination
                """
                generate_id(imprt, entity)

            if entity.code in ["visit", "observation"]:
                set_parent_id_from_line_no(imprt, entity)

            fields = {
                ef.field.name_field: ef.field
                for ef in entity.fields
                if ef.field.dest_field != None
            }
            insert_fields = set()
            # insert_fields = {fields["id_station"]}
            for field_name, mapping in imprt.fieldmapping.items():
                if field_name not in fields:  # not a destination field
                    continue
                field = fields[field_name]
                column_src = mapping.get("column_src", None)
                if field.multi:
                    if not set(column_src).isdisjoint(imprt.columns):
                        insert_fields |= {field}
                else:
                    if (
                        column_src in imprt.columns
                        or mapping.get("default_value", None) is not None
                    ):
                        insert_fields |= {field}
            if entity.code == "site":
                insert_fields |= {fields["s__geom_4326"], fields["s__geom_local"]}
                insert_fields -= {fields["s__types_site"]}
            elif entity.code == "visit":
                insert_fields |= {fields["id_dataset"]}
                # These fields are associated with habitat as necessary to find the corresponding station,
                # but they are not inserted in habitat destination so we need to manually remove them.
                # insert_fields -= {fields["unique_id_sinp_station"], fields["id_station_source"]}
                # FIXME:
                # if not selected_fields.get("unique_id_sinp_generate", False):
                #    # even if not selected, add uuid column to force insert of NULL values instead of default generation of uuid
                #    insert_fields |= {fields["unique_id_sinp_habitat"]}
            names = ["id_import"] + [
                get_dest_col_name(field.dest_field) for field in insert_fields
            ]
            select_stmt = (
                sa.select(
                    sa.literal(imprt.id_import).label("id_import"),
                    *[
                        transient_table.c[field.dest_field].label(
                            get_dest_col_name(field.dest_field)
                        )
                        for field in insert_fields
                    ],
                )
                .where(transient_table.c.id_import == imprt.id_import)
                .where(transient_table.c[entity.validity_column] == True)
                # .where(transient_table.c.id_station.is_not(None))
            )
            destination_table = entity.get_destination_table()
            print(destination_table)
            print(destination_table.columns)
            batch_size = current_app.config["IMPORT"]["INSERT_BATCH_SIZE"]
            batch_count = ceil(imprt.source_count / batch_size)
            row_count = 0
            for batch in range(batch_count):
                min_line_no = batch * batch_size
                max_line_no = (batch + 1) * batch_size
                insert_stmt = sa.insert(destination_table).from_select(
                    names=names,
                    select=select_stmt.filter(
                        transient_table.c["line_no"] >= min_line_no,
                        transient_table.c["line_no"] < max_line_no,
                    ),
                )
                row_count += db.session.execute(insert_stmt).rowcount
                yield (batch + 1) / batch_count
            imprt.statistics.update({f"{entity.code}_count": row_count})

    @staticmethod
    def remove_data_from_destination(imprt: TImports) -> None:
        pass

    @staticmethod
    def report_plot(imprt: TImports) -> StandaloneEmbedJson:
        return None

    @staticmethod
    def compute_bounding_box(imprt: TImports) -> None:
        pass

    # Following methods not present in ImportActions

    @staticmethod
    def check_parents_consistency(imprt):
        entity_site, entity_visit, _ = get_entities(imprt)

        _, selected_site_fields, _ = get_mapping_data(imprt, entity_site)

        if "s__id_base_site" in selected_site_fields:
            check_entity_data_consistency(
                imprt,
                entity_site,
                selected_site_fields,
                selected_site_fields["s__id_base_site"],
            )
        if "s__uuid_base_site" in selected_site_fields:
            check_entity_data_consistency(
                imprt,
                entity_site,
                selected_site_fields,
                selected_site_fields["s__uuid_base_site"],
            )

        _, selected_visit_fields, _ = get_mapping_data(imprt, entity_visit)

        if "v__id_base_visit" in selected_visit_fields:
            check_entity_data_consistency(
                imprt,
                entity_visit,
                selected_visit_fields,
                selected_visit_fields["v__id_base_visit"],
            )
        if "v__uuid_base_visit" in selected_visit_fields:
            check_entity_data_consistency(
                imprt,
                entity_visit,
                selected_visit_fields,
                selected_visit_fields["v__uuid_base_visit"],
            )

    @staticmethod
    def dataframe_checks(imprt, df, entity, fields):
        updated_cols = set({})
        updated_cols |= check_types(
            imprt, entity, df, fields
        )  # FIXME do not check site and visit uuid twice

        updated_cols |= check_required_values(imprt, entity, df, fields)

        return updated_cols

    @staticmethod
    def check_site_dataframe(imprt: TImports, config):
        """
        Check the site data before importing.

        List of checks and data operations (in order of execution):
        - check types
        - check required values
        - convert geom columns
        - check geography
        - check if given geometries are valid (see ST_VALID in PostGIS)

        Parameters
        ----------
        imprt : TImports
            The import to check.

        """

        entity_site, _, _ = get_entities(imprt)

        fields, _, source_cols = get_mapping_data(imprt, entity_site)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity_site, source_cols)

        updated_cols |= MonitoringImportActions.dataframe_checks(imprt, df, entity_site, fields)

        geom_field_name = config.get("site", {}).get("geom_field_name")
        if geom_field_name:
            updated_cols |= check_geometry(
                imprt,
                entity_site,
                df,
                file_srid=imprt.srid,
                geom_4326_field=fields[f"s__{geom_field_name}_4326"],
                geom_local_field=fields[f"s__{geom_field_name}_local"],
                wkt_field=fields[f"s__{geom_field_name}"],
            )

        update_transient_data_from_dataframe(imprt, entity_site, updated_cols, df)

    @staticmethod
    def check_visit_dataframe(imprt: TImports):
        """
        Check the visit data before importing.

        List of checks and data operations (in order of execution):
        - check datasets
        - check types
        - check required values

        Parameters
        ----------
        imprt : TImports
            The import to check.

        """

        _, entity_visit, _ = get_entities(imprt)

        fields, _, source_cols = get_mapping_data(imprt, entity_visit)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity_visit, source_cols)

        updated_cols |= MonitoringImportActions.dataframe_checks(imprt, df, entity_visit, fields)

        updated_cols |= check_datasets(
            imprt,
            entity_visit,
            df,
            uuid_field=fields["unique_dataset_id"],
            id_field=fields["id_dataset"],
            module_code=imprt.destination.module.module_code,  # Or use MONITORINGS ?
        )

        update_transient_data_from_dataframe(imprt, entity_visit, updated_cols, df)

    @staticmethod
    def check_observation_dataframe(imprt: TImports):
        """
        Check the observation data before importing.

        List of checks and data operations (in order of execution):
        - check types
        - check required values

        Parameters
        ----------
        imprt : TImports
            The import to check.

        """

        _, _, entity_observation = get_entities(imprt)

        fields, _, source_cols = get_mapping_data(imprt, entity_observation)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity_observation, source_cols)

        updated_cols |= MonitoringImportActions.dataframe_checks(
            imprt, df, entity_observation, fields
        )

        update_transient_data_from_dataframe(imprt, entity_observation, updated_cols, df)
