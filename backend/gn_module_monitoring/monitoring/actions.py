from math import ceil
import re
from geonature.core.gn_monitoring.models import (
    TBaseSites,
    TBaseVisits,
    TObservations,
    cor_site_type,
)
from geonature.core.imports.checks.dataframe.cast import check_types
from geonature.core.imports.checks.dataframe.core import check_datasets, check_required_values
from geonature.core.imports.checks.dataframe.geometry import check_geometry
from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
)
from geonature.core.imports.checks.sql.parent import set_parent_line_no
from gn_module_monitoring.monitoring.models import (
    TMonitoringObservations,
    TMonitoringSites,
    TMonitoringVisits,
)
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
    _, entity_fields, _ = get_mapping_data(imprt, entity)

    for field_name in [
        f"id_base_{entity.code}",
        f"uuid_base_{entity.code}",
    ]:
        if field_name in entity_fields:
            disable_duplicated_rows(
                imprt,
                entity,
                entity_fields,
                entity_fields[field_name],
            )

    if entity.parent is not None:
        parent_code = entity.parent.code
        _, parent_fields, _ = get_mapping_data(imprt, entity.parent)
        set_parent_line_no(
            imprt,
            parent_entity=entity.parent,
            child_entity=entity,
            id_parent=f"id_base_{parent_code}",
            parent_line_no=f"{parent_code}_line_no",
            fields=[
                entity_fields.get(f"id_base_{parent_code}"),
                parent_fields.get(f"uuid_base_{parent_code}"),
            ],
        )


def get_entity_model(entity: Entity):
    if entity.code == "site":
        return TBaseSites
    elif entity.code == "visit":
        return TBaseVisits
    elif entity.code == "observation":
        return TObservations

    return None


def get_entity_model_complements(entity: Entity):
    if entity.code == "site":
        return TMonitoringSites
    elif entity.code == "visit":
        return TMonitoringVisits
    elif entity.code == "observation":
        return TMonitoringObservations

    return None


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

        entity_site, entity_visit, entity_observation = get_entities(imprt)

        check_entity_sql(imprt, entity_site)
        check_entity_sql(imprt, entity_visit)
        check_entity_sql(imprt, entity_observation)

    @staticmethod
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

        entity_site, entity_visit, entity_observation = get_entities(imprt)

        # Maybe better here than in import_data_to_destination ?
        generate_id(imprt, entity_site)
        generate_id(imprt, entity_visit)

        set_parent_id_from_line_no(imprt, entity_visit)
        set_parent_id_from_line_no(imprt, entity_observation)

        for entity in entities.values():
            print(f"--------- {entity.code}")

            fields = {
                ef.field.name_field: ef.field
                for ef in entity.fields
                if ef.field.dest_field != None
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
                    if (
                        column_src in imprt.columns
                        or mapping.get("default_value", None) is not None
                    ):
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

            core_fields = []
            core_dest_col_names = ["id_import"]
            complement_fields = []
            destination_model = get_entity_model(entity)
            destination_table = destination_model.__table__
            destination_col_names = list(destination_table.columns.keys())
            for field in entity_fields:
                col_name = get_dest_col_name(field.dest_field)
                if col_name in destination_col_names and col_name not in core_dest_col_names:
                    core_fields.append(field)
                    core_dest_col_names.append(col_name)
                else:
                    complement_fields.append(field)

            core_select_cols = [sa.literal(imprt.id_import).label("id_import")]
            core_select_cols.extend(
                transient_table.c[field.dest_field].label(get_dest_col_name(field.dest_field))
                for field in core_fields
            )

            if entity.code == "visit":
                core_select_cols.append(sa.literal(imprt.destination.id_module).label("id_module"))
                core_dest_col_names.append("id_module")

            core_select_stmt = (
                sa.select(*core_select_cols)
                .where(transient_table.c.id_import == imprt.id_import)
                .where(transient_table.c[entity.validity_column] == True)
                .order_by(
                    transient_table.c.line_no
                )  # Required for the process of inserting observation complements
            )

            id_col_name = f"id_base_{entity.code}"
            json_args = []
            for field in complement_fields:
                json_args.extend(
                    [get_dest_col_name(field.dest_field), transient_table.c[field.dest_field]]
                )

            complement_select_stmt = None
            model_complements = get_entity_model_complements(entity)
            if model_complements is not None and len(json_args):
                cols = [sa.func.json_build_object(*json_args).label("data")]
                if entity.code != "observation":
                    cols.insert(0, transient_table.c[id_col_name])
                complement_select_stmt = (
                    sa.select(*cols)
                    .where(transient_table.c.id_import == imprt.id_import)
                    .where(transient_table.c[entity.validity_column] == True)
                    .order_by(
                        transient_table.c.line_no
                    )  # Required for the process of inserting observation complements
                )

            types_site_select_stmt = None
            if entity.code == "site":
                types_site_select_stmt = (
                    sa.select(
                        transient_table.c["id_base_site"],
                        sa.func.unnest(transient_table.c["s__types_site"]).label("id_type_site"),
                    )
                    .where(transient_table.c.id_import == imprt.id_import)
                    .where(transient_table.c[entity.validity_column] == True)
                )

            batch_size = current_app.config["IMPORT"]["INSERT_BATCH_SIZE"]
            batch_count = ceil(imprt.source_count / batch_size)
            row_count = 0
            for batch in range(batch_count):
                min_line_no = batch * batch_size
                max_line_no = (batch + 1) * batch_size
                core_select = core_select_stmt.filter(
                    transient_table.c["line_no"] >= min_line_no,
                    transient_table.c["line_no"] < max_line_no,
                )

                if entity.code == "observation":
                    compiled_select_core = core_select.compile(
                        compile_kwargs={"literal_binds": True}
                    )
                    sql_query_obs = f"""
                    INSERT INTO {destination_table.fullname} ({' ,'.join(core_dest_col_names)}) {compiled_select_core} 
                    RETURNING id_observation
                    """
                    result = db.session.execute(sa.text(sql_query_obs))
                    created_ids = result.scalars().all()
                    row_count += result.rowcount

                    if complement_select_stmt is not None:
                        # CTE pour récupérer les observations insérées, avec un row_number basé sur id_observation
                        obs_ordered_cte = (
                            sa.select(
                                destination_table.c.id_observation,
                                sa.func.row_number()
                                .over(order_by=destination_table.c.id_observation)
                                .label("row_num"),
                            )
                            .where(destination_table.c.id_observation.in_(created_ids))
                            .cte("obs_ordered")
                        )

                        # CTE pour le complement_select_stmt, en ajoutant un row_number basé sur line_no
                        comp_cte = (
                            complement_select_stmt.add_columns(
                                sa.func.row_number()
                                .over(order_by=transient_table.c.line_no)
                                .label("row_num")
                            )
                            .filter(
                                transient_table.c["line_no"] >= min_line_no,
                                transient_table.c["line_no"] < max_line_no,
                            )
                            .cte("comp_cte")
                        )

                        # On effectue la jointure sur row_num pour associer chaque observation à la ligne complémentaire correspondante
                        final_select = sa.select(
                            obs_ordered_cte.c.id_observation, comp_cte.c.data
                        ).select_from(
                            obs_ordered_cte.join(
                                comp_cte, obs_ordered_cte.c.row_num == comp_cte.c.row_num
                            )
                        )

                        # Insertion dans model_complements via from_select
                        final_insert = sa.insert(model_complements).from_select(
                            ["id_observation", "data"], final_select
                        )

                        db.session.execute(final_insert)
                else:
                    core_insert_stmt = sa.insert(destination_model).from_select(
                        names=core_dest_col_names,
                        select=core_select,
                    )
                    row_count += db.session.execute(core_insert_stmt).rowcount
                    if complement_select_stmt is not None:
                        db.session.execute(
                            sa.insert(model_complements).from_select(
                                names=[id_col_name, "data"],
                                select=complement_select_stmt.filter(
                                    transient_table.c["line_no"] >= min_line_no,
                                    transient_table.c["line_no"] < max_line_no,
                                ),
                            )
                        )

                    if types_site_select_stmt is not None:
                        db.session.execute(
                            sa.insert(cor_site_type).from_select(
                                ["id_base_site", "id_type_site"],
                                types_site_select_stmt.filter(
                                    transient_table.c["line_no"] >= min_line_no,
                                    transient_table.c["line_no"] < max_line_no,
                                ),
                            )
                        )

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

        if "id_base_site" in selected_site_fields:
            check_entity_data_consistency(
                imprt,
                entity_site,
                selected_site_fields,
                selected_site_fields["id_base_site"],
            )
        if "uuid_base_site" in selected_site_fields:
            check_entity_data_consistency(
                imprt,
                entity_site,
                selected_site_fields,
                selected_site_fields["uuid_base_site"],
            )

        _, selected_visit_fields, _ = get_mapping_data(imprt, entity_visit)

        if "id_base_visit" in selected_visit_fields:
            check_entity_data_consistency(
                imprt,
                entity_visit,
                selected_visit_fields,
                selected_visit_fields["id_base_visit"],
            )
        if "uuid_base_visit" in selected_visit_fields:
            check_entity_data_consistency(
                imprt,
                entity_visit,
                selected_visit_fields,
                selected_visit_fields["uuid_base_visit"],
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
