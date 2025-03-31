from .entity_import_actions_utils import EntityImportActionsUtils

from geonature.core.imports.models import Entity, TImports

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
)

from geonature.core.imports.checks.sql import (
    check_duplicate_uuid,
    check_existing_uuid,
    set_id_parent_from_destination,
)
from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
    compute_bounding_box,
)

from geonature.core.imports.checks.dataframe.geometry import check_geometry


class SiteImportActions:
    ENTITY_CODE = "site"
    ID_FIELD = "id_base_site"
    UUID_FIELD = "uuid_base_site"

    @staticmethod
    def check_sql(imprt: TImports):
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        _, entity_site_fields, _ = get_mapping_data(imprt, entity_site)

        # Check existing uuid
        if SiteImportActions.UUID_FIELD in entity_site_fields:
            check_existing_uuid(
                imprt,
                entity_site,
                entity_site_fields.get(SiteImportActions.UUID_FIELD),
                skip=True,  # TODO config
            )

        # Disable duplicated definition row
        if SiteImportActions.UUID_FIELD in entity_site_fields:
            disable_duplicated_rows(
                imprt,
                entity_site,
                entity_site_fields,
                entity_site_fields.get(SiteImportActions.UUID_FIELD),
            )

        # Check duplicate uuid
        if SiteImportActions.UUID_FIELD in entity_site_fields:
            check_duplicate_uuid(
                imprt, entity_site, entity_site_fields.get(SiteImportActions.UUID_FIELD)
            )

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

        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)

        fields, _, source_cols = get_mapping_data(imprt, entity_site)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity_site, source_cols)

        updated_cols |= EntityImportActionsUtils.dataframe_checks(imprt, df, entity_site, fields)

        geom_field_name = config.get(SiteImportActions.ENTITY_CODE, {}).get("geom_field_name")
        if geom_field_name:
            geom_field_name__local = f"s__{geom_field_name}_local"
            geom_field_name__4326 = f"s__{geom_field_name}_4326"
            geom_field_name__wkt = f"s__{geom_field_name}"
            updated_cols |= check_geometry(
                imprt,
                entity_site,
                df,
                file_srid=imprt.srid,
                geom_4326_field=fields[geom_field_name__4326],
                geom_local_field=fields[geom_field_name__local],
                wkt_field=fields[geom_field_name__wkt],
            )

        update_transient_data_from_dataframe(imprt, entity_site, updated_cols, df)

    @staticmethod
    def generate_id(imprt: TImports):
        EntityImportActionsUtils.generate_id(
            imprt, EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        )

    @staticmethod
    def check_entity_data_consistency(imprt: TImports):
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        _, entity_site_fields, _ = get_mapping_data(imprt, entity_site)

        if SiteImportActions.ID_FIELD in entity_site_fields:
            check_entity_data_consistency(
                imprt,
                entity_site,
                entity_site_fields,
                entity_site_fields.get(SiteImportActions.ID_FIELD),
            )
        if SiteImportActions.UUID_FIELD in entity_site_fields:
            check_entity_data_consistency(
                imprt,
                entity_site,
                entity_site_fields,
                entity_site_fields.get(SiteImportActions.UUID_FIELD),
            )

    @staticmethod
    def compute_bounding_box(imprt: TImports):
        return compute_bounding_box(
            imprt=imprt,
            geom_entity_code="site",
            geom_4326_field_name="s__geom",
        )
