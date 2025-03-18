from math import ceil
from geonature.core.imports.checks.dataframe.cast import check_types
from geonature.core.imports.checks.dataframe.core import check_datasets, check_required_values
from geonature.core.imports.checks.dataframe.geometry import check_geometry
from geonature.core.imports.checks.sql.extra import check_entity_data_consistency
import sqlalchemy as sa
from sqlalchemy import select

from geonature.core.imports.actions import ImportActions
from geonature.core.imports.checks.sql.core import check_orphan_rows, init_rows_validity
from geonature.core.imports.models import BibFields, Entity, EntityField, TImports
from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
)

from geonature.utils.env import db
from geonature.utils.sentry import start_sentry_child

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

    @staticmethod
    def import_data_to_destination(imprt: TImports) -> None:
        raise NotImplementedError

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
        print("selected_site_fields", selected_site_fields)

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
        print("selected_visit_fields", selected_visit_fields)

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
