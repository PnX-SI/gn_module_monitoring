from gn_module_monitoring.monitoring.import_actions.base import BaseImportActions
from flask import current_app
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
    do_nomenclatures_mapping,
    generate_missing_uuid_for_id_origin,
)
from geonature.core.imports.utils import (
    get_mapping_data,
    compute_bounding_box,
)

from geonature.core.imports.checks.sql.user import map_observer_matching

from .geometry import (
    check_wkt_geometries,
    compute_geom_local,
    get_geom_field_name,
)


class SiteImportActions(BaseImportActions):
    ENTITY_CODE = "site"
    FIELD_PREFIX = "s__"
    TABLE_NAME = "t_base_sites"
    ID_FIELD = "id_base_site"
    ID_ORIGIN_FIELD = "id_base_site_origin"
    LINE_NO = "site_line_no"
    UUID_FIELD = "uuid_base_site"
    GEOMETRY_FIELD = "s__geom"
    ALTITUDE_MIN_FIELD = "s__altitude_min"
    ALTITUDE_MAX_FIELD = "s__altitude_max"
    LINE_NO = "site_line_no"
    ID_INVENTOR_FIELD = "s__id_inventor"

    @staticmethod
    def check_pre(imprt: TImports):
        """Mappings avant le schéma étendu : nomenclatures, observateur du site."""
        entity = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        _, fieldmapped_fields, _ = get_mapping_data(imprt, entity)

        do_nomenclatures_mapping(imprt, entity, fieldmapped_fields, fill_with_defaults=False)
        if SiteImportActions.ID_INVENTOR_FIELD in fieldmapped_fields:
            map_observer_matching(imprt, entity, fieldmapped_fields["s__id_inventor"])

    @staticmethod
    def check_post(imprt: TImports):
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


        EntityImportActionsUtils.check_cd_nom_on_taxonomy_field(
            imprt, SiteImportActions.ENTITY_CODE
        )

    @staticmethod
    def check_df_batch(imprt: TImports, entity: Entity, df) -> set:
        """
        Check the site data of one batch, in the dataframe.

        List of checks (in order of execution):
        - check geography (WKT, bounding box, 4326 geometry)

        Parameters
        ----------
        imprt : TImports
            The import to check.
        entity : Entity
            The site entity.
        df : pandas.DataFrame
            The site data of the batch (loaded and written back by the core).

        Returns
        -------
        set
            Names of the columns modified in ``df``.
        """
        entity_fields, _, _ = get_mapping_data(imprt, entity)

        # Save column names where the data was changed in the dataframe
        updated_cols = set()

        from gn_module_monitoring.modules import get_module

        site_entity = get_module(imprt.destination.code).entities[SiteImportActions.ENTITY_CODE]
        geom_field_name = site_entity.data.get("geom_field_name")
        if geom_field_name:
            # WKT source (`src_s__geom`, éventuellement écrit depuis x/y) -> géométrie 4326 (`s__geom`)
            updated_cols |= check_wkt_geometries(
                imprt,
                entity,
                df,
                file_srid=imprt.srid,
                wkt_field=entity_fields[f"s__{geom_field_name}"],
                geom_4326_field=entity_fields[f"s__{geom_field_name}"],
            )

        return updated_cols

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
        from gn_module_monitoring.monitoring.import_actions.visit_actions import (
            VisitImportActions,
        )

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

        # Colonne transitoire de la géométrie 4326 : `dest_field` du champ s__geom
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        fields, _, _ = get_mapping_data(imprt, entity_site)

        return compute_bounding_box(
            imprt=imprt,
            geom_entity_code=SiteImportActions.ENTITY_CODE,
            geom_4326_field_name__transient=fields[SiteImportActions.GEOMETRY_FIELD].dest_field,
            geom_4326_field_name__destination="geom",  # colonne de t_base_sites
            child_entity_code=deepest_child_entity_code,
        )

    @staticmethod
    def check_and_compute_geometries(imprt: TImports):
        entity_site = EntityImportActionsUtils.get_entity(imprt, SiteImportActions.ENTITY_CODE)
        fields, _, _ = get_mapping_data(imprt, entity_site)

        compute_geom_local(
            imprt,
            entity_site,
            geom_4326_field=fields[SiteImportActions.GEOMETRY_FIELD],
            geom_field_name=get_geom_field_name(imprt, SiteImportActions.ENTITY_CODE),
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
