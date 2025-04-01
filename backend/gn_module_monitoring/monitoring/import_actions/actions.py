from math import ceil
import re
from geonature.core.gn_monitoring.models import (
    TBaseSites,
    TBaseVisits,
    TObservations,
    cor_site_type,
)

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


from geonature.utils.env import db

from bokeh.embed.standalone import StandaloneEmbedJson
from flask import current_app

import typing


from .entity_import_actions_utils import EntityImportActionsUtils
from gn_module_monitoring.monitoring.import_actions.site_actions import SiteImportActions
from gn_module_monitoring.monitoring.import_actions.visit_actions import VisitImportActions
from gn_module_monitoring.monitoring.import_actions.observation_actions import (
    ObservationImportActions,
)


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
        SiteImportActions.check_entity_data_consistency(imprt)
        VisitImportActions.check_entity_data_consistency(imprt)

        # We run dataframes checks before SQL checks in order to avoid
        # check_types overriding generated values during SQL checks.
        SiteImportActions.check_dataframe(imprt, config)
        VisitImportActions.check_dataframe(imprt)
        ObservationImportActions.check_dataframe(imprt)

        SiteImportActions.check_sql(imprt)
        VisitImportActions.check_sql(imprt)
        ObservationImportActions.check_sql(imprt)

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

        SiteImportActions.generate_id(imprt)
        VisitImportActions.generate_id(imprt)
        ObservationImportActions.generate_id(imprt)

        VisitImportActions.set_parent_id_from_line_no(imprt)
        ObservationImportActions.set_parent_id_from_line_no(imprt)

        for entity in entities.values():
            print(f"--------- {entity.code}")

            entity_fields = EntityImportActionsUtils.get_destination_fields(imprt, entity)

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
    def compute_bounding_box(imprt: TImports):
        # Problem with bounding box: the field doesn't have the same name between the transient table and the destination table
        # It  might be the problem
        pass
