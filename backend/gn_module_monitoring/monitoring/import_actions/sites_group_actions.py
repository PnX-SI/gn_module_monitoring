from .entity_import_actions_utils import EntityImportActionsUtils

from geonature.core.imports.models import TImports

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
    generate_entity_id,
    generate_missing_uuid,
    generate_missing_uuid_for_id_origin,
    check_duplicate_uuid,
    check_existing_uuid,
    check_altitudes,
)

from geonature.core.imports.checks.sql.geo import convert_geom_columns
from geonature.core.imports.checks.sql.nomenclature import do_nomenclatures_mapping

from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
    compute_bounding_box,
)

from geonature.core.imports.checks.dataframe.geometry import check_geometry

from geonature.core.imports.checks.sql.user import map_observer_matching


class SitesGroupImportActions:
    ENTITY_CODE = "sites_group"
    TABLE_NAME = "t_sites_groups"
    ID_FIELD = "id_sites_group"
    ID_ORIGIN_FIELD = "id_sites_group_origin"
    LINE_NO = "sites_group_line_no"
    UUID_FIELD = "uuid_sites_group"
    GEOMETRY_FIELD = "g__geom"
    GEOMETRY_4326_FIELD = "g__geom_4326"
    GEOMETRY_LOCAL_FIELD = "g__geom_local"
    ALTITUDE_MIN_FIELD = "g__altitude_min"
    ALTITUDE_MAX_FIELD = "g__altitude_max"

    @staticmethod
    def check_sql(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, SitesGroupImportActions.ENTITY_CODE)
        entity_fields, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        if SitesGroupImportActions.UUID_FIELD in fieldmapped_fields:
            uuid_field = fieldmapped_fields.get(SitesGroupImportActions.UUID_FIELD)
            # Check existing uuid
            check_existing_uuid(
                imprt,
                entity,
                uuid_field,
                skip=True,  # TODO config
            )

            # Disable duplicated definition row
            disable_duplicated_rows(
                imprt,
                entity,
                fieldmapped_fields,
                uuid_field,
            )

            # Check duplicate uuid
            check_duplicate_uuid(imprt, entity, uuid_field)

        if SitesGroupImportActions.ID_ORIGIN_FIELD in fieldmapped_fields:
            generate_missing_uuid_for_id_origin(
                imprt,
                entity_fields.get(SitesGroupImportActions.UUID_FIELD),
                entity_fields.get(SitesGroupImportActions.ID_ORIGIN_FIELD),
            )
        generate_missing_uuid(
            imprt,
            entity,
            entity_fields.get(SitesGroupImportActions.UUID_FIELD),
            whereclause=None,
        )

        if SitesGroupImportActions.ID_ORIGIN_FIELD in fieldmapped_fields:
            disable_duplicated_rows(
                imprt,
                entity,
                fieldmapped_fields,
                entity_fields.get(SitesGroupImportActions.ID_ORIGIN_FIELD),
            )

        SitesGroupImportActions.check_and_compute_geometries(imprt)

        SitesGroupImportActions.check_altitudes(imprt)

        do_nomenclatures_mapping(imprt, entity, fieldmapped_fields, fill_with_defaults=False)

    @staticmethod
    def check_dataframe(imprt: TImports, config):
        """
        Check the site group data before importing.

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
        entity = EntityImportActionsUtils.get_entity(imprt, SitesGroupImportActions.ENTITY_CODE)

        entity_fields, _, source_cols = get_mapping_data(imprt, entity)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity, source_cols)

        updated_cols |= EntityImportActionsUtils.dataframe_checks(imprt, df, entity, entity_fields)

        geom_field_name = config.get(SitesGroupImportActions.ENTITY_CODE, {}).get(
            "geom_field_name"
        )
        if geom_field_name:
            geom_field_name__local = f"g__{geom_field_name}_local"
            geom_field_name__4326 = f"g__{geom_field_name}_4326"
            geom_field_name__wkt = f"g__{geom_field_name}"
            updated_cols |= check_geometry(
                imprt,
                entity,
                df,
                file_srid=imprt.srid,
                geom_4326_field=entity_fields[geom_field_name__4326],
                geom_local_field=entity_fields[geom_field_name__local],
                wkt_field=entity_fields[geom_field_name__wkt],
            )

        update_transient_data_from_dataframe(imprt, entity, updated_cols, df)

    @staticmethod
    def generate_id(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, SitesGroupImportActions.ENTITY_CODE)
        generate_entity_id(
            imprt,
            entity,
            "gn_monitoring",
            "t_sites_groups",
            "uuid_sites_group",
            "id_sites_group",
        )

    @staticmethod
    def check_entity_data_consistency(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, SitesGroupImportActions.ENTITY_CODE)

        _, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        if SitesGroupImportActions.ID_FIELD in fieldmapped_fields:
            check_entity_data_consistency(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(SitesGroupImportActions.ID_FIELD),
            )
        if SitesGroupImportActions.UUID_FIELD in fieldmapped_fields:
            check_entity_data_consistency(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(SitesGroupImportActions.UUID_FIELD),
            )

    @staticmethod
    def compute_bounding_box(imprt: TImports):
        import geojson
        from gn_module_monitoring.monitoring.import_actions.site_actions import SiteImportActions

        def get_bounding_box(points):
            x_coordinates, y_coordinates = zip(*points)

            return [
                [
                    (min(x_coordinates), max(y_coordinates)),
                    (min(x_coordinates), min(y_coordinates)),
                    (max(x_coordinates), min(y_coordinates)),
                    (max(x_coordinates), max(y_coordinates)),
                    (min(x_coordinates), max(y_coordinates)),
                ]
            ]

        # Problem with bounding box: the field doesn't have the same name between the transient table and the destination table
        # It  might be the problem

        # TMonitoringSites which has a foreign key with TMonitoringSitesGroups isn't part of GeoNature core
        # thus can't be called from core function compute_bounding_box(). We aggregate two boxes instead.
        sites_group_bounding_box = compute_bounding_box(
            imprt=imprt,
            geom_entity_code=SitesGroupImportActions.ENTITY_CODE,
            geom_4326_field_name__transient=SitesGroupImportActions.GEOMETRY_FIELD,
            geom_4326_field_name__destination=EntityImportActionsUtils.get_destination_column_name(
                SitesGroupImportActions.GEOMETRY_FIELD
            ),
        )
        children_bounding_box = SiteImportActions.compute_bounding_box(imprt)

        if sites_group_bounding_box and children_bounding_box:
            return geojson.Polygon(
                get_bounding_box(
                    list(
                        geojson.utils.coords(
                            geojson.GeometryCollection(
                                [sites_group_bounding_box, children_bounding_box]
                            )
                        )
                    )
                )
            )

        return sites_group_bounding_box or children_bounding_box

    @staticmethod
    def check_and_compute_geometries(imprt: TImports):
        entity_site = EntityImportActionsUtils.get_entity(
            imprt, SitesGroupImportActions.ENTITY_CODE
        )
        fields, _, _ = get_mapping_data(imprt, entity_site)

        convert_geom_columns(
            imprt,
            entity_site,
            geom_4326_field=fields[SitesGroupImportActions.GEOMETRY_4326_FIELD],
            geom_local_field=fields[SitesGroupImportActions.GEOMETRY_LOCAL_FIELD],
        )

    @staticmethod
    def check_altitudes(imprt: TImports):
        entity_sites_group = EntityImportActionsUtils.get_entity(
            imprt, SitesGroupImportActions.ENTITY_CODE
        )
        fields, _, _ = get_mapping_data(imprt, entity_sites_group)

        check_altitudes(
            imprt,
            entity_sites_group,
            fields[SitesGroupImportActions.ALTITUDE_MIN_FIELD],
            fields[SitesGroupImportActions.ALTITUDE_MAX_FIELD],
        )
