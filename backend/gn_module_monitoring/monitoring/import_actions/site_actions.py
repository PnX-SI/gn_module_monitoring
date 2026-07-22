import sqlalchemy as sa
from flask import current_app
from .entity_import_actions_utils import EntityImportActionsUtils

from geonature.core.imports.models import TImports

from geonature.core.imports.checks.errors import ImportCodeError
from geonature.core.imports.checks.sql.utils import report_erroneous_rows
from geonature.core.imports.checks.sql.parent import (
    set_parent_line_no,
    check_no_parent_entity,
    set_id_parent_from_destination,
    check_erroneous_parent_entities,
)

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
    generate_entity_id,
    generate_missing_uuid,
    generate_missing_uuid_for_id_origin,
    check_duplicate_uuid,
    check_existing_uuid,
    check_altitudes,
    set_parent_id_from_line_no,
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


class SiteImportActions:
    ENTITY_CODE = "site"
    TABLE_NAME = "t_base_sites"
    ID_FIELD = "id_base_site"
    ID_ORIGIN_FIELD = "id_base_site_origin"
    LINE_NO = "site_line_no"
    UUID_FIELD = "uuid_base_site"
    GEOMETRY_FIELD = "s__geom"
    GEOMETRY_4326_FIELD = "s__geom_4326"
    GEOMETRY_LOCAL_FIELD = "s__geom_local"
    ALTITUDE_MIN_FIELD = "s__altitude_min"
    ALTITUDE_MAX_FIELD = "s__altitude_max"
    PARENT_ID_FIELD = "id_sites_group"
    PARENT_UUID_FIELD = "uuid_sites_group"
    PARENT_LINE_NO = "sites_group_line_no"
    LINE_NO = "site_line_no"
    ID_INVENTOR_FIELD = "s__id_inventor"

    @staticmethod
    def check_sql(imprt: TImports, isSitesGroups, isSitesGroupMandatory):
        from gn_module_monitoring.monitoring.import_actions.sites_group_actions import (
            SitesGroupImportActions,
        )

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

        if SiteImportActions.ID_ORIGIN_FIELD in fieldmapped_fields:
            generate_missing_uuid_for_id_origin(
                imprt,
                entity_fields.get(SiteImportActions.UUID_FIELD),
                entity_fields.get(SiteImportActions.ID_ORIGIN_FIELD),
            )
        generate_missing_uuid(
            imprt,
            entity,
            entity_fields.get(SiteImportActions.UUID_FIELD),
            whereclause=None,
        )

        if SiteImportActions.ID_ORIGIN_FIELD in fieldmapped_fields:
            disable_duplicated_rows(
                imprt,
                entity,
                fieldmapped_fields,
                entity_fields.get(SiteImportActions.ID_ORIGIN_FIELD),
            )

        SiteImportActions.check_and_compute_geometries(imprt)

        SiteImportActions.check_altitudes(imprt)

        do_nomenclatures_mapping(imprt, entity, fieldmapped_fields, fill_with_defaults=False)

        ## process parent uuid and id only if the module accepts sites groups

        if isSitesGroups:
            set_id_parent_from_destination(
                imprt,
                parent_entity=entity.parent,
                entity=entity,
                id_field=entity_fields.get(SitesGroupImportActions.ID_FIELD),
                fields=[
                    entity_fields.get(SitesGroupImportActions.UUID_FIELD),
                ],
            )

            # Wire parent child
            set_parent_line_no(
                imprt,
                parent_entity=entity.parent,
                entity=entity,
                parent_line_no=SitesGroupImportActions.LINE_NO,
                fields=[
                    entity_fields.get(SitesGroupImportActions.ID_ORIGIN_FIELD),
                    entity_fields.get(SitesGroupImportActions.UUID_FIELD),
                ],
            )
            SiteImportActions.check_parent_validity(imprt, isSitesGroupMandatory)

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
    def set_parent_id_from_line_no(imprt: TImports):
        from gn_module_monitoring.monitoring.import_actions.sites_group_actions import (
            SitesGroupImportActions,
        )

        entity = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        set_parent_id_from_line_no(
            imprt,
            entity=entity,
            parent_line_no_field_name=SitesGroupImportActions.LINE_NO,
            parent_id_field_name=SitesGroupImportActions.ID_FIELD,
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
        from gn_module_monitoring.monitoring.import_actions.visit_actions import VisitImportActions

        # Problem with bounding box: the field doesn't have the same name between the transient table and the destination table
        # It  might be the problem

        deepest_child_entity_code = SiteImportActions.ENTITY_CODE

        if EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, ObservationImportActions.ENTITY_CODE
        ):
            deepest_child_entity_code = ObservationImportActions.ENTITY_CODE
        elif EntityImportActionsUtils.is_entity_defined_in_import(
            imprt, VisitImportActions.ENTITY_CODE
        ):
            deepest_child_entity_code = VisitImportActions.ENTITY_CODE

        return compute_bounding_box(
            imprt=imprt,
            geom_entity_code=SiteImportActions.ENTITY_CODE,
            geom_4326_field_name__transient=SiteImportActions.GEOMETRY_FIELD,
            geom_4326_field_name__destination=EntityImportActionsUtils.get_destination_column_name(
                SiteImportActions.GEOMETRY_FIELD
            ),
            child_entity_code=deepest_child_entity_code,
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

    @staticmethod
    def check_parent_validity(imprt: TImports, isSitesGroupMandatory: bool):
        from gn_module_monitoring.monitoring.import_actions.sites_group_actions import (
            SitesGroupImportActions,
        )

        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        entity_sites_group = EntityImportActionsUtils.get_entity(
            imprt, SitesGroupImportActions.ENTITY_CODE
        )

        # A site referencing a sites group (by UUID or origin identifier) that could
        # be resolved neither in the destination nor on another line of the file is
        # erroneous, even when the sites group is optional: the provided reference
        # would otherwise be silently ignored.
        transient_table = imprt.destination.get_transient_table()
        entity_fields, _, _ = get_mapping_data(imprt, entity_site)
        for ref_field_name in (
            SitesGroupImportActions.UUID_FIELD,
            SitesGroupImportActions.ID_ORIGIN_FIELD,
        ):
            ref_field = entity_fields.get(ref_field_name)
            if ref_field is None:
                continue
            report_erroneous_rows(
                imprt,
                entity_site,
                error_type=ImportCodeError.NO_PARENT_ENTITY,
                error_column=ref_field_name,
                whereclause=sa.and_(
                    transient_table.c[entity_site.validity_column].is_(True),
                    # no sites group defined on the same line...
                    transient_table.c[entity_sites_group.validity_column].is_(None),
                    # ...the reference was not found in the destination...
                    transient_table.c[SitesGroupImportActions.ID_FIELD].is_(None),
                    # ...nor on another line of the file...
                    transient_table.c[SitesGroupImportActions.LINE_NO].is_(None),
                    # ...although a reference was provided
                    transient_table.c[ref_field.source_field].isnot(None),
                ),
            )

        if isSitesGroupMandatory:
            check_no_parent_entity(
                imprt,
                parent_entity=entity_sites_group,
                entity=entity_site,
                id_parent=SitesGroupImportActions.ID_FIELD,
                parent_line_no=SitesGroupImportActions.LINE_NO,
            )

        check_erroneous_parent_entities(
            imprt,
            parent_entity=entity_sites_group,
            entity=entity_site,
            parent_line_no=SitesGroupImportActions.LINE_NO,
        )
