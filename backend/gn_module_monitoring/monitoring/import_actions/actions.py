from math import ceil

from geonature.core.imports.models import BibFields
from geoalchemy2 import Geometry
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
from geonature.core.imports.actions import (
    ImportActions,
    ImportStatisticsLabels,
    import_hook,
)
from geonature.core.imports.models import Entity, TImports
from geonature.core.imports.checks.dataframe.cast import check_types
from geonature.core.imports.checks.dataframe.core import check_required_values
from geonature.core.imports.utils import get_mapping_data
from geonature.core.gn_monitoring.models import CorVisitObserver


from geonature.utils.env import db

from bokeh.embed.standalone import StandaloneEmbedJson
from flask import current_app

import typing


from .entity_import_actions_utils import EntityImportActionsUtils
from gn_module_monitoring.command.imports.constant import geom_local_column_name
from gn_module_monitoring.monitoring.import_actions.geometry import get_geom_field_name
from gn_module_monitoring.monitoring.import_actions.site_actions import (
    SiteImportActions,
)
from gn_module_monitoring.monitoring.import_actions.visit_actions import (
    VisitImportActions,
)
from gn_module_monitoring.monitoring.import_actions.observation_actions import (
    ObservationImportActions,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert


def get_entities(imprt: TImports) -> typing.Tuple[Entity, Entity, Entity]:
    entity_site = Entity.query.filter_by(code="site").one()
    entity_visit = Entity.query.filter_by(code="visit").one()
    entity_observation = Entity.query.filter_by(
        code="observation", id_destination=imprt.destination.id_destination
    ).one()
    return entity_site, entity_visit, entity_observation


def get_fields_to_cast(fields: dict, transient_table) -> dict:
    """
    Champs de `fields` à caster par check_types : tous, sauf ceux dont la colonne de destination dans la
    table transitoire est une géométrie. Les champs sans colonne de destination ne sont pas concernés.
    """
    return {
        name: field
        for name, field in fields.items()
        if not (
            field.dest_field
            and field.dest_field in transient_table.c
            and isinstance(transient_table.c[field.dest_field].type, Geometry)
        )
    }


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
        return [
            {"key": "site_count", "value": "Nombre de sites importés"},
            {"key": "visit_count", "value": "Nombre de visites importées"},
            {"key": "observation_count", "value": "Nombre d'observations importées"},
            {"key": "taxa_count", "value": "Nombre de taxons importés"},
        ]

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
        from gn_module_monitoring.modules import get_module

        customs = get_module(destination.code).substitutions
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
    def preprocess_transient_data(imprt: TImports, df) -> None:
        pass

    @staticmethod
    def get_source_cols(imprt: TImports, entity: Entity) -> typing.List[str]:
        # All the fields are loaded: the CEL conditions may use any field of the entity
        return [ef.field.source_field for ef in entity.fields if ef.field.source_field is not None]

    @staticmethod
    @import_hook(progress=0.1)
    def check_transient_data_pre(task, logger, imprt: TImports, update_progress) -> None:
        ImportActions.check_transient_data_pre(task, logger, imprt, update_progress)

        isVisit = EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, VisitImportActions.ENTITY_CODE
        )

        # We first check site and visit consistency in order to avoid checking
        # incoherent data
        SiteImportActions.check_entity_data_consistency(imprt)
        if isVisit:
            VisitImportActions.check_entity_data_consistency(imprt)

    @staticmethod
    @import_hook(progress=0.4)
    def check_transient_data_df_batch(
        task, logger, imprt: TImports, entity: Entity, df, update_progress
    ) -> set:
        # We run dataframes checks before SQL checks in order to avoid
        # check_types overriding generated values during SQL checks.
        fields, _, _ = get_mapping_data(imprt, entity)

        # Les champs géométrie (colonne transitoire de type Geometry) sont lus et convertis par les
        # contrôles géométrie : check_types ne doit pas les caster.
        fields_to_cast = get_fields_to_cast(fields, imprt.destination.get_transient_table())
        updated_cols = check_types(
            imprt, entity, df, fields_to_cast
        )  # FIXME do not check site and visit uuid twice
        if entity.code == SiteImportActions.ENTITY_CODE:
            # x/y -> WKT source (si WKT vide), après check_types, avant le contrôle des champs requis
            updated_cols |= SiteImportActions.fill_wkt_from_xy(imprt, entity, df)
        updated_cols |= check_required_values(imprt, entity, df, fields)

        if entity.code == SiteImportActions.ENTITY_CODE:
            updated_cols |= SiteImportActions.check_dataframe(imprt, entity, df)
        elif entity.code == VisitImportActions.ENTITY_CODE:
            updated_cols |= VisitImportActions.check_dataframe(imprt, entity, df)
        return updated_cols

    @staticmethod
    @import_hook(progress=0.5)
    def check_transient_data_post(task, logger, imprt: TImports, update_progress) -> None:
        isVisit = EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, VisitImportActions.ENTITY_CODE
        )
        isObservation = EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, ObservationImportActions.ENTITY_CODE
        )

        SiteImportActions.check_sql(imprt)
        if isVisit:
            VisitImportActions.check_sql(imprt)
        if isObservation:
            ObservationImportActions.check_sql(imprt)

    @staticmethod
    def import_data_to_destination(imprt: TImports) -> None:
        # Import local : évite le cycle actions -> modules.entities -> models -> actions

        isVisit = EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, VisitImportActions.ENTITY_CODE
        )
        isObservation = EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, ObservationImportActions.ENTITY_CODE
        )

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
        SiteImportActions.generate_id(imprt)
        if isVisit:
            VisitImportActions.generate_id(imprt)
        if isObservation:
            ObservationImportActions.generate_id(imprt)

        if isVisit:
            VisitImportActions.set_parent_id_from_line_no(imprt)
        if isObservation:
            ObservationImportActions.set_parent_id_from_line_no(imprt)

        for entity in entities.values():
            print(f"--------- {entity.code}")

            entity_fields = EntityImportActionsUtils.get_destination_fields(imprt, entity)

            core_dest_col_names = ["id_import", "id_digitiser"]
            core_select_cols = [
                sa.literal(imprt.id_import).label("id_import"),
                sa.literal(imprt.authors[0].id_role).label("id_digitiser"),
            ]
            complement_fields = []
            destination_model = get_entity_model(entity)
            destination_table = destination_model.__table__
            destination_col_names = list(destination_table.columns.keys())

            # Add default values for hidden fields (lockstep with core_dest_col_names)
            default_values = EntityImportActionsUtils.get_default_values_for_hidden_fields(
                imprt, entity.code
            )
            for field, default_value in default_values.items():
                dest_col_name = EntityImportActionsUtils.get_destination_column_name(
                    field.dest_field
                )
                if dest_col_name not in core_dest_col_names:
                    core_dest_col_names.append(dest_col_name)
                    core_select_cols.append(sa.literal(default_value).label(dest_col_name))

            # Add core fields (lockstep with core_dest_col_names)
            for field in entity_fields:
                dest_col_name = EntityImportActionsUtils.get_destination_column_name(
                    field.dest_field
                )
                if (
                    dest_col_name in destination_col_names
                    and dest_col_name not in core_dest_col_names
                ):
                    core_dest_col_names.append(dest_col_name)
                    core_select_cols.append(
                        transient_table.c[field.dest_field].label(dest_col_name)
                    )
                else:
                    complement_fields.append(field)

            # Géométrie locale de l'entité : colonne annexe de la table transitoire, sans bib_fields
            geom_field_name = get_geom_field_name(imprt, entity.code)
            if geom_field_name is not None:
                geom_local_column = geom_local_column_name(geom_field_name)
                if (
                    geom_local_column in transient_table.c
                    and geom_local_column in destination_col_names
                    and geom_local_column not in core_dest_col_names
                ):
                    core_dest_col_names.append(geom_local_column)
                    core_select_cols.append(
                        transient_table.c[geom_local_column].label(geom_local_column)
                    )

            if entity.code == "visit":
                core_dest_col_names.append("id_module")
                core_select_cols.append(sa.literal(imprt.destination.id_module).label("id_module"))

            core_select_stmt = (
                sa.select(*core_select_cols)
                .where(transient_table.c.id_import == imprt.id_import)
                .where(transient_table.c[entity.validity_column] == True)
                .order_by(transient_table.c.line_no)
            )

            # IF NO ENTITY to INSERT continue
            count_entity_to_import = db.session.scalar(
                sa.select(sa.func.count("*")).select_from(core_select_stmt.subquery())
            )
            if count_entity_to_import < 1:
                continue

            id_col_name = f"id_base_{entity.code}"
            json_args = []
            for field in complement_fields:
                json_args.extend(
                    [
                        EntityImportActionsUtils.get_destination_column_name(
                            field.dest_field
                        ),
                        transient_table.c[field.dest_field],
                    ]
                )

            complement_select_stmt = None
            model_complements = get_entity_model_complements(entity)
            if model_complements is not None:
                cols = [sa.text("'{}'::JSONB as data")]
                if len(json_args):
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
                    sql_query_obs = (
                        pg_insert(destination_table)
                        .from_select(names=core_dest_col_names, select=core_select)
                        .returning(destination_table.c.id_observation)
                    )
                    result = db.session.execute(sql_query_obs)
                    created_ids = result.scalars().all()
                    row_count += result.rowcount

                    if complement_select_stmt is not None:
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

                        final_select = sa.select(
                            obs_ordered_cte.c.id_observation, comp_cte.c.data
                        ).select_from(
                            obs_ordered_cte.join(
                                comp_cte,
                                obs_ordered_cte.c.row_num == comp_cte.c.row_num,
                            )
                        )

                        final_insert = sa.insert(model_complements).from_select(
                            ["id_observation", "data"], final_select
                        )
                        db.session.execute(final_insert)
                else:
                    core_insert_stmt = sa.insert(destination_model).from_select(
                        names=core_dest_col_names, select=core_select
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

            if entity.code == "visit" and MonitoringImportActions.is_observer_mapping_enabled():
                # If the visit observers were mapped
                if "v__observers" in imprt.fieldmapping:
                    # If visit was mapped with an observers set as a constant
                    if imprt.fieldmapping["v__observers"].get("constant_value", None) is not None:
                        db.session.execute(
                            sa.insert(CorVisitObserver).from_select(
                                ["id_base_visit", "id_role"],
                                sa.select(
                                    transient_table.c.id_base_visit,
                                    sa.func.unnest(transient_table.c["v__observers"]).label(
                                        "id_role"
                                    ),
                                )
                                .where(transient_table.c["v__observers"] != None)
                                .where(transient_table.c.id_import == imprt.id_import)
                                .where(transient_table.c[entity.validity_column] == True),
                            )
                        )
                    else:
                        # If visit observers are originate from the source file and were mapped during the import process
                        ImportActions.bind_matched_observers(
                            imprt,
                            transient_table,
                            "src_v__observers",
                            "id_base_visit",
                            CorVisitObserver,
                            ["id_base_visit", "id_role"],
                        )

        imprt.statistics.update(ObservationImportActions.compute_taxa_statistics(imprt))

        # filter empty statistics
        statistics_0_keys = []
        for key, value in imprt.statistics.items():
            if value == 0:
                statistics_0_keys.append(key)
        for key in statistics_0_keys:
            imprt.statistics.pop(key)

    @staticmethod
    def report_plot(imprt: TImports) -> StandaloneEmbedJson:
        return None

    @staticmethod
    def compute_bounding_box(imprt: TImports):
        # Problem with bounding box: the field doesn't have the same name between the transient table and the destination table
        # It  might be the problem
        return SiteImportActions.compute_bounding_box(imprt)
