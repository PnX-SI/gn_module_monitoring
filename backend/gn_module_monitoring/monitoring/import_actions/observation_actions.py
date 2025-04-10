from .entity_import_actions_utils import EntityImportActionsUtils
from geonature.core.imports.checks.sql.parent import set_parent_line_no

from geonature.core.imports.models import Entity, TImports

from geonature.core.gn_monitoring.models import TObservations
from geonature.utils.env import db
import sqlalchemy as sa

from geonature.core.imports.checks.sql.extra import (
    check_entity_data_consistency,
    disable_duplicated_rows,
)

from geonature.core.imports.checks.sql import (
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


class ObservationImportActions:
    ENTITY_CODE = "observation"
    TABLE_NAME = "t_observations"
    ID_FIELD = "id_observation"
    UUID_FIELD = "uuid_observation"
    PARENT_ID_FIELD = "id_base_visit"
    PARENT_UUID_FIELD = "uuid_base_visit"
    PARENT_LINE_NO = "visit_line_no"

    @staticmethod
    def check_sql(imprt):
        entity_observation = EntityImportActionsUtils.get_entity(
            imprt, ObservationImportActions.ENTITY_CODE
        )
        fields, entity_observation_fields, _ = get_mapping_data(imprt, entity_observation)

        # Check existing uuid
        if ObservationImportActions.UUID_FIELD in entity_observation_fields:
            check_existing_uuid(
                imprt,
                entity_observation,
                entity_observation_fields.get(ObservationImportActions.UUID_FIELD),
                skip=True,  # TODO config
            )

        # Disable duplicated definition row
        if ObservationImportActions.UUID_FIELD in entity_observation_fields:
            disable_duplicated_rows(
                imprt,
                entity_observation,
                entity_observation_fields,
                entity_observation_fields.ge(ObservationImportActions.UUID_FIELD),
            )

        # Check duplicate uuid
        if ObservationImportActions.UUID_FIELD in entity_observation_fields:
            check_duplicate_uuid(
                imprt,
                entity_observation,
                entity_observation_fields.get(ObservationImportActions.UUID_FIELD),
            )
        # Wire parent child
        if entity_observation.parent is not None:
            set_parent_line_no(
                imprt,
                parent_entity=entity_observation.parent,
                child_entity=entity_observation,
                id_parent=ObservationImportActions.PARENT_UUID_FIELD,
                parent_line_no=ObservationImportActions.PARENT_LINE_NO,
                fields=[
                    entity_observation_fields.get(ObservationImportActions.PARENT_UUID_FIELD),
                ],
            )

        ## process parent uuid and id
        set_id_parent_from_destination(
            imprt,
            parent_entity=entity_observation.parent,
            child_entity=entity_observation,
            id_field=fields.get(ObservationImportActions.PARENT_ID_FIELD),
            fields=[
                entity_observation_fields.get(ObservationImportActions.PARENT_UUID_FIELD),
            ],
        )

        ObservationImportActions.check_parent_validity(imprt)

    @staticmethod
    def check_dataframe(imprt: TImports):
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

        entity_observation = EntityImportActionsUtils.get_entity(
            imprt, ObservationImportActions.ENTITY_CODE
        )

        fields, _, source_cols = get_mapping_data(imprt, entity_observation)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        ### Dataframe checks
        df = load_transient_data_in_dataframe(imprt, entity_observation, source_cols)

        updated_cols |= EntityImportActionsUtils.dataframe_checks(
            imprt, df, entity_observation, fields
        )

        update_transient_data_from_dataframe(imprt, entity_observation, updated_cols, df)

    @staticmethod
    def generate_id(imprt: TImports):
        EntityImportActionsUtils.generate_id(
            imprt,
            EntityImportActionsUtils.get_entity(imprt, ObservationImportActions.ENTITY_CODE),
            ObservationImportActions.TABLE_NAME,
            ObservationImportActions.UUID_FIELD,
            ObservationImportActions.ID_FIELD,
        )

    @staticmethod
    def set_parent_id_from_line_no(imprt: TImports):
        EntityImportActionsUtils.set_parent_id_from_line_no(
            imprt, EntityImportActionsUtils.get_entity(imprt, ObservationImportActions.ENTITY_CODE)
        )

    @staticmethod
    def compute_taxa_statistics(imprt: TImports):
        # TODO: Improve this
        return {
            "taxa_count": (
                db.session.scalar(
                    sa.select(sa.func.count(sa.distinct(TObservations.cd_nom))).where(
                        TObservations.id_import == imprt.id_import
                    )
                )
            ),
        }

    @staticmethod
    def check_parent_validity(imprt: TImports):
        from gn_module_monitoring.monitoring.import_actions.visit_actions import (
            VisitImportActions,
        )

        entity_observation = EntityImportActionsUtils.get_entity(
            imprt, ObservationImportActions.ENTITY_CODE
        )
        entity_visit = EntityImportActionsUtils.get_entity(imprt, VisitImportActions.ENTITY_CODE)

        check_no_parent_entity(
            imprt,
            parent_entity=entity_visit,
            child_entity=entity_observation,
            id_parent=VisitImportActions.ID_FIELD,
            parent_line_no=VisitImportActions.LINE_NO,
        )

        check_erroneous_parent_entities(
            imprt,
            parent_entity=entity_visit,
            child_entity=entity_observation,
            parent_line_no=VisitImportActions.LINE_NO,
        )
