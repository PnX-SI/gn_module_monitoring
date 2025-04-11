from .entity_import_actions_utils import EntityImportActionsUtils
from geonature.core.imports.checks.sql.parent import set_parent_line_no

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
    generate_entity_id,
    generate_missing_uuid,
    set_parent_id_from_line_no,
)

from geonature.core.imports.checks.sql import (
    check_dates,
    check_duplicate_uuid,
    check_erroneous_parent_entities,
    check_existing_uuid,
    check_no_parent_entity,
    set_id_parent_from_destination,
)
from geonature.core.imports.utils import (
    get_mapping_data,
    load_transient_data_in_dataframe,
    update_transient_data_from_dataframe,
)

from geonature.core.imports.models import Entity, TImports

from geonature.core.imports.checks.dataframe.core import check_datasets, check_required_values


class VisitImportActions:
    ENTITY_CODE = "visit"
    TABLE_NAME = "t_base_visits"
    ID_FIELD = "id_base_visit"
    LINE_NO = "visit_line_no"
    UUID_FIELD = "uuid_base_visit"
    DATE_MIN_FIELD = "v__visit_date_min"
    DATE_MAX_FIELD = "v__visit_date_max"
    PARENT_ID_FIELD = "id_base_site"
    PARENT_UUID_FIELD = "uuid_base_site"
    PARENT_LINE_NO = "site_line_no"
    LINE_NO = "visit_line_no"

    @staticmethod
    def check_sql(imprt):
        from gn_module_monitoring.monitoring.import_actions.site_actions import (
            SiteImportActions,
        )

        entity = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        entity_fields, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        # Check existing uuid
        if VisitImportActions.UUID_FIELD in fieldmapped_fields:
            check_existing_uuid(
                imprt,
                entity,
                fieldmapped_fields.get(VisitImportActions.UUID_FIELD),
                skip=True,  # TODO config
            )

        # Disable duplicated definition row
        if VisitImportActions.UUID_FIELD in fieldmapped_fields:
            disable_duplicated_rows(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(VisitImportActions.UUID_FIELD),
            )

        # Check duplicate uuid
        if VisitImportActions.UUID_FIELD in fieldmapped_fields:
            check_duplicate_uuid(
                imprt, entity, fieldmapped_fields.get(VisitImportActions.UUID_FIELD)
            )

        generate_missing_uuid(
            imprt,
            entity,
            entity_fields.get(VisitImportActions.UUID_FIELD),
            whereclause=None,
        )

        # Wire parent child
        set_parent_line_no(
            imprt,
            parent_entity=entity.parent,
            entity=entity,
            parent_line_no=SiteImportActions.LINE_NO,
            fields=[
                entity_fields.get(SiteImportActions.UUID_FIELD),
            ],
        )

        ## process parent uuid and id
        set_id_parent_from_destination(
            imprt,
            parent_entity=entity.parent,
            entity=entity,
            id_field=entity_fields.get(SiteImportActions.ID_FIELD),
            fields=[
                entity_fields.get(SiteImportActions.UUID_FIELD),
            ],
        )

        VisitImportActions.check_dates(imprt)

        VisitImportActions.check_parent_validity(imprt)

    @staticmethod
    def check_dataframe(imprt: TImports):
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

        entity = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)

        entity_fields, _, source_cols = get_mapping_data(imprt, entity)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity, source_cols)

        updated_cols |= EntityImportActionsUtils.dataframe_checks(imprt, df, entity, entity_fields)

        updated_cols |= check_datasets(
            imprt,
            entity,
            df,
            uuid_field=entity_fields["unique_dataset_id"],
            id_field=entity_fields["id_dataset"],
            module_code=imprt.destination.module.module_code,
            object_code="MONITORINGS_VISITES",
        )

        update_transient_data_from_dataframe(imprt, entity, updated_cols, df)

    ## UUID visit and site should not be mandatory !

    @staticmethod
    def generate_id(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        generate_entity_id(
            imprt,
            entity,
            "gn_monitoring",
            "t_base_visits",
            "uuid_base_visit",
            "id_base_visit",
        )

    @staticmethod
    def set_parent_id_from_line_no(imprt: TImports):
        from gn_module_monitoring.monitoring.import_actions.site_actions import (
            SiteImportActions,
        )

        entity = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        set_parent_id_from_line_no(
            imprt,
            entity=entity,
            parent_line_no_field_name=SiteImportActions.LINE_NO,
            parent_id_field_name=SiteImportActions.ID_FIELD,
        )

    @staticmethod
    def check_entity_data_consistency(imprt: TImports):
        entity = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)

        _, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        if VisitImportActions.ID_FIELD in fieldmapped_fields:
            check_entity_data_consistency(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(VisitImportActions.ID_FIELD),
            )
        if VisitImportActions.UUID_FIELD in fieldmapped_fields:
            check_entity_data_consistency(
                imprt,
                entity,
                fieldmapped_fields,
                fieldmapped_fields.get(VisitImportActions.UUID_FIELD),
            )

    @staticmethod
    def check_dates(imprt: TImports):
        entity_visit = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        fields, _, _ = get_mapping_data(imprt, entity_visit)
        check_dates(
            imprt,
            entity_visit,
            fields[VisitImportActions.DATE_MIN_FIELD],
            fields[VisitImportActions.DATE_MAX_FIELD],
        )

    @staticmethod
    def check_parent_validity(imprt: TImports):
        from gn_module_monitoring.monitoring.import_actions.site_actions import (
            SiteImportActions,
        )

        entity_visit = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)

        check_no_parent_entity(
            imprt,
            parent_entity=entity_site,
            entity=entity_visit,
            id_parent=SiteImportActions.ID_FIELD,
            parent_line_no=SiteImportActions.LINE_NO,
        )

        check_erroneous_parent_entities(
            imprt,
            parent_entity=entity_site,
            entity=entity_visit,
            parent_line_no=SiteImportActions.LINE_NO,
        )
