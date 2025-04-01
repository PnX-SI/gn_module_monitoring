from .entity_import_actions_utils import EntityImportActionsUtils
from geonature.core.imports.checks.sql.parent import set_parent_line_no

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
)

from geonature.core.imports.models import Entity, TImports

from geonature.core.imports.checks.dataframe.core import check_datasets, check_required_values


class VisitImportActions:
    ENTITY_CODE = "visit"
    TABLE_NAME = "t_base_visits"
    ID_FIELD = "id_base_visit"
    UUID_FIELD = "uuid_base_visit"
    PARENT_ID_FIELD = "id_base_site"
    PARENT_UUID_FIELD = "uuid_base_site"
    PARENT_LINE_NO = "site_line_no"

    @staticmethod
    def check_sql(imprt):
        entity_visit = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        fields, entity_visit_fields, _ = get_mapping_data(imprt, entity_visit)

        # Check existing uuid
        if VisitImportActions.UUID_FIELD in entity_visit_fields:
            check_existing_uuid(
                imprt,
                entity_visit,
                entity_visit_fields.get(VisitImportActions.UUID_FIELD),
                skip=True,  # TODO config
            )

        # Disable duplicated definition row
        if VisitImportActions.UUID_FIELD in entity_visit_fields:
            disable_duplicated_rows(
                imprt,
                entity_visit,
                entity_visit_fields,
                entity_visit_fields.get(VisitImportActions.UUID_FIELD),
            )

        # Check duplicate uuid
        if VisitImportActions.UUID_FIELD in entity_visit_fields:
            check_duplicate_uuid(
                imprt, entity_visit, entity_visit_fields.get(VisitImportActions.UUID_FIELD)
            )

        # Wire parent child
        set_parent_line_no(
            imprt,
            parent_entity=entity_visit.parent,
            child_entity=entity_visit,
            id_parent=VisitImportActions.PARENT_UUID_FIELD,
            parent_line_no=VisitImportActions.PARENT_LINE_NO,
            fields=[
                entity_visit_fields.get(VisitImportActions.PARENT_UUID_FIELD),
            ],
        )

        ## process parent uuid and id
        set_id_parent_from_destination(
            imprt,
            parent_entity=entity_visit.parent,
            child_entity=entity_visit,
            id_field=fields.get(VisitImportActions.PARENT_ID_FIELD),
            fields=[
                entity_visit_fields.get(VisitImportActions.PARENT_UUID_FIELD),
            ],
        )

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

        entity_visit = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)

        fields, _, source_cols = get_mapping_data(imprt, entity_visit)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity_visit, source_cols)

        updated_cols |= EntityImportActionsUtils.dataframe_checks(imprt, df, entity_visit, fields)

        updated_cols |= check_datasets(
            imprt,
            entity_visit,
            df,
            uuid_field=fields["unique_dataset_id"],
            id_field=fields["id_dataset"],
            module_code=imprt.destination.module.module_code,
        )

        update_transient_data_from_dataframe(imprt, entity_visit, updated_cols, df)

    @staticmethod
    def generate_id(imprt: TImports):
        EntityImportActionsUtils.generate_id(
            imprt,
            EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE),
            VisitImportActions.TABLE_NAME,
            VisitImportActions.UUID_FIELD,
            VisitImportActions.ID_FIELD,
        )

    @staticmethod
    def set_parent_id_from_line_no(imprt: TImports):
        EntityImportActionsUtils.set_parent_id_from_line_no(
            imprt, EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)
        )

    @staticmethod
    def check_entity_data_consistency(imprt: TImports):
        entity_visit = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)

        _, entity_visit_fields, _ = get_mapping_data(imprt, entity_visit)

        if VisitImportActions.ID_FIELD in entity_visit_fields:
            check_entity_data_consistency(
                imprt,
                entity_visit,
                entity_visit_fields,
                entity_visit_fields.get(VisitImportActions.ID_FIELD),
            )
        if VisitImportActions.UUID_FIELD in entity_visit_fields:
            check_entity_data_consistency(
                imprt,
                entity_visit,
                entity_visit_fields,
                entity_visit_fields.get(VisitImportActions.UUID_FIELD),
            )
