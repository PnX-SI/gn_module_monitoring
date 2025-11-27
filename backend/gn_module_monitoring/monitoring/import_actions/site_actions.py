from .entity_import_actions_utils import EntityImportActionsUtils

from geonature.core.imports.models import Entity, TImports

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
    generate_entity_id,
    generate_missing_uuid,
)

from geonature.core.imports.checks.sql import (
    check_altitudes,
    check_duplicate_uuid,
    check_existing_uuid,
    convert_geom_columns,
)
from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
    compute_bounding_box,
)

from geonature.core.imports.checks.dataframe.geometry import check_geometry

from geonature.core.imports.checks.sql.user import map_observer_matching


class SiteImportActions:
    ENTITY_CODE = "site"
    TABLE_NAME = "t_base_sites"
    ID_FIELD = "id_base_site"
    LINE_NO = "site_line_no"
    UUID_FIELD = "uuid_base_site"
    GEOMETRY_FIELD = "s__geom"
    GEOMETRY_4326_FIELD = "s__geom_4326"
    GEOMETRY_LOCAL_FIELD = "s__geom_local"
    ALTITUDE_MIN_FIELD = "s__altitude_min"
    ALTITUDE_MAX_FIELD = "s__altitude_max"
    LINE_NO = "site_line_no"
    ID_INVENTOR_FIELD = "s__id_inventor"

    @staticmethod
    def check_sql(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        entity_fields, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        # Check existing uuid
        if SiteImportActions.UUID_FIELD in fieldmapped_fields:
            check_existing_uuid(
                imprt,
                entity,
                fieldmapped_fields.get(SiteImportActions.UUID_FIELD),
                skip=True,  # TODO config
            )

        # Disable duplicated definition row
        if SiteImportActions.UUID_FIELD in fieldmapped_fields:
            disable_duplicated_rows(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(SiteImportActions.UUID_FIELD),
            )

        # Check duplicate uuid
        if SiteImportActions.UUID_FIELD in fieldmapped_fields:
            check_duplicate_uuid(
                imprt, entity, fieldmapped_fields.get(SiteImportActions.UUID_FIELD)
            )

        generate_missing_uuid(
            imprt,
            entity,
            entity_fields.get(SiteImportActions.UUID_FIELD),
            whereclause=None,
        )

        SiteImportActions.check_and_compute_geometries(imprt)

        SiteImportActions.check_altitudes(imprt)

        if SiteImportActions.ID_INVENTOR_FIELD in fieldmapped_fields:
            map_observer_matching(imprt, entity, fieldmapped_fields["s__id_inventor"])

    @staticmethod
    def check_dataframe(imprt: TImports, config):
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

        entity = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)

        entity_fields, _, source_cols = get_mapping_data(imprt, entity)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity, source_cols)

        updated_cols |= EntityImportActionsUtils.dataframe_checks(imprt, df, entity, entity_fields)

        geom_field_name = config.get(SiteImportActions.ENTITY_CODE, {}).get("geom_field_name")
        if geom_field_name:
            geom_field_name__local = f"s__{geom_field_name}_local"
            geom_field_name__4326 = f"s__{geom_field_name}_4326"
            geom_field_name__wkt = f"s__{geom_field_name}"
            updated_cols |= check_geometry(
                imprt,
                entity,
                df,
                file_srid=imprt.srid,
                geom_4326_field=entity_fields[geom_field_name__4326],
                geom_local_field=entity_fields[geom_field_name__local],
                wkt_field=entity_fields[geom_field_name__wkt],
                latitude_field=entity_fields["y"],
                longitude_field=entity_fields["x"],
            )

        update_transient_data_from_dataframe(imprt, entity, updated_cols, df)

    @staticmethod
    def generate_id(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        generate_entity_id(
            imprt,
            entity,
            "gn_monitoring",
            "t_base_sites",
            "uuid_base_site",
            "id_base_site",
        )

    @staticmethod
    def check_entity_data_consistency(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        _, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        if SiteImportActions.ID_FIELD in fieldmapped_fields:
            check_entity_data_consistency(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(SiteImportActions.ID_FIELD),
            )
        if SiteImportActions.UUID_FIELD in fieldmapped_fields:
            check_entity_data_consistency(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(SiteImportActions.UUID_FIELD),
            )

    @staticmethod
    def compute_bounding_box(imprt: TImports):
        from gn_module_monitoring.monitoring.import_actions.observation_actions import (
            ObservationImportActions,
        )

        # Problem with bounding box: the field doesn't have the same name between the transient table and the destination table
        # It  might be the problem
        return compute_bounding_box(
            imprt=imprt,
            geom_entity_code=SiteImportActions.ENTITY_CODE,
            geom_4326_field_name__transient=SiteImportActions.GEOMETRY_FIELD,
            geom_4326_field_name__destination=EntityImportActionsUtils.get_destination_column_name(
                SiteImportActions.GEOMETRY_FIELD
            ),
            child_entity_code=ObservationImportActions.ENTITY_CODE,
        )

    @staticmethod
    def check_and_compute_geometries(imprt: TImports):
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        fields, _, _ = get_mapping_data(imprt, entity_site)

        convert_geom_columns(
            imprt,
            entity_site,
            geom_4326_field=fields[SiteImportActions.GEOMETRY_4326_FIELD],
            geom_local_field=fields[SiteImportActions.GEOMETRY_LOCAL_FIELD],
        )

    @staticmethod
    def check_altitudes(imprt: TImports):
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        fields, _, _ = get_mapping_data(imprt, entity_site)

        check_altitudes(
            imprt,
            entity_site,
            fields[SiteImportActions.ALTITUDE_MIN_FIELD],
            fields[SiteImportActions.ALTITUDE_MAX_FIELD],
        )
