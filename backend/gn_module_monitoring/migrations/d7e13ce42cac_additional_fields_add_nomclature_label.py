"""Additional fields add nomclature _label

Revision ID: d7e13ce42cac
Revises: 3d39820c9ab7
Create Date: 2026-08-11 16:09:58.674427

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from gn_module_monitoring.command.utils import installed_modules
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.config.utils import get_specific_properties

# revision identifiers, used by Alembic.
revision = "d7e13ce42cac"
down_revision = "3d39820c9ab7"
branch_labels = None
depends_on = None


def upgrade():
    from gn_module_monitoring.monitoring.definitions import MonitoringModels_dict
    from gn_module_monitoring.config.utils import get_specific_properties

    monitoring_object = [
        "module",
        "sites_group",
        "site",
        "visit",
        "observation",
        "individual",
        "marking",
        "observation_detail",
    ]
    conn = op.get_bind()

    # Get all monitoring modules
    rows = conn.execute(text("""
        SELECT tm.id_module , tm.module_code
        FROM gn_commons.t_modules tm
        JOIN gn_monitoring.t_module_complements tmc
        ON tm.id_module = tmc.id_module
    """)).fetchall()

    for module in rows:
        log.info(f"upgrade module {module['module_code']}")
        # Get config
        config = get_config(module["module_code"], force=True)
        if not config:
            continue

        # Get nomenclature fields for each object
        nomenclature_fields = {}
        for object_type in monitoring_object:
            model_class = MonitoringModels_dict[object_type]
            nomenclature_fields[object_type] = []
            if not object_type in config:
                continue

            specific_properties = get_specific_properties(model_class, config, object_type)

            for attribut_name, attribut_value in specific_properties.items():
                if attribut_value.get("type_util", None) == "nomenclature":
                    nomenclature_fields[object_type].append(attribut_name)

        # ---- process nomenclature fields
        # Process module
        if len(nomenclature_fields["module"]) > 0:
            sql = upgrade_module(nomenclature_fields["module"], module["id_module"])
            op.execute(sql)

        # Process sites_group
        if len(nomenclature_fields["sites_group"]) > 0:
            sql = upgrade_sites_group(nomenclature_fields["sites_group"], module["id_module"])
            op.execute(sql)

        # Process sites
        if len(nomenclature_fields["site"]) > 0:
            sql = upgrade_site(nomenclature_fields["site"], module["id_module"])
            op.execute(sql)

        # Process visit
        if len(nomenclature_fields["visit"]) > 0:
            sql = upgrade_visit(nomenclature_fields["visit"], module["id_module"])
            op.execute(sql)

        # Process observations
        if len(nomenclature_fields["observation"]) > 0:
            sql = upgrade_observation(nomenclature_fields["observation"], module["id_module"])
            op.execute(sql)

        # Process observations_detail
        if len(nomenclature_fields["observation_detail"]) > 0:
            sql = upgrade_observation_detail(
                nomenclature_fields["observation_detail"], module["id_module"]
            )
            op.execute(sql)
        # Process individual -> NA pour le moment car le champ additional_data n'existe pas

        # Process marking
        if len(nomenclature_fields["marking"]) > 0:
            sql = upgrade_marking(nomenclature_fields["marking"], module["id_module"])
            op.execute(sql)


def downgrade():
    tables_names = [
        "t_module_complements",
        "t_sites_groups",
        "t_site_complements",
        "t_visit_complements",
        "t_observation_complements",
        "t_observation_details",
        "t_marking_events",
    ]
    for table_name in tables_names:
        op.execute(generate_downgrade(table_name))


def upgrade_module(fields_list, id_module):
    sql = text("""
    WITH final_data AS (
        SELECT tsc.id_module , tsc.DATA  || jsonb_object_agg(json_key, json_content) as data
        FROM gn_monitoring.t_module_complements tsc
        CROSS JOIN LATERAL jsonb_each(tsc.data) e(jkey, value)
        JOIN LATERAL (
            SELECT '_label_' || e.jkey AS json_key,  string_agg(tn.label_default, '|')   AS json_content
            FROM (
                SELECT e.value #>> '{}' AS id_nomenclature
                WHERE jsonb_typeof(e.value) <> 'array'
                UNION ALL
                SELECT jsonb_array_elements_text(e.value)
                WHERE jsonb_typeof(e.value) = 'array'
            ) v
            JOIN ref_nomenclatures.t_nomenclatures tn
            ON tn.id_nomenclature::text = v.id_nomenclature
        ) lbl ON e.jkey = ANY(:fields_list)
        WHERE tsc.id_module = :id_module
        GROUP BY  tsc.id_module , tsc.data
    )
    UPDATE gn_monitoring.t_module_complements tsc
    SET data = final_data.data
    FROM final_data
    WHERE tsc.id_module = final_data.id_module;
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def upgrade_sites_group(fields_list, id_module):
    sql = text("""
     with s as (
        SELECT distinct sg.id_sites_group
        FROM gn_monitoring.t_sites_groups sg
        join gn_monitoring.cor_sites_group_module csgm
        ON sg.id_sites_group = csgm.id_sites_group
        WHERE csgm.id_module = :id_module
    ) , final_data AS (
    SELECT tsc.id_sites_group , tsc.DATA || jsonb_object_agg(json_key, json_content) AS data
    FROM gn_monitoring.t_sites_groups tsc
    join s on s.id_sites_group = tsc.id_sites_group
    CROSS JOIN LATERAL jsonb_each(tsc.data) e(jkey, value)
    JOIN LATERAL (
        SELECT '_label_' || e.jkey AS json_key,  string_agg(tn.label_default, '|')   AS json_content
        FROM (
            SELECT e.value #>> '{}' AS id_nomenclature
            WHERE jsonb_typeof(e.value) <> 'array'
            UNION ALL
            SELECT jsonb_array_elements_text(e.value)
            WHERE jsonb_typeof(e.value) = 'array'
        ) v
        JOIN ref_nomenclatures.t_nomenclatures tn
        ON tn.id_nomenclature::text = v.id_nomenclature
    ) lbl ON e.jkey  = ANY(:fields_list)
    GROUP BY  tsc.id_sites_group , tsc.data
  )
  update gn_monitoring.t_sites_groups tsc
    SET data = final_data.data
    FROM final_data
    WHERE tsc.id_sites_group = final_data.id_sites_group;
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def upgrade_site(fields_list, id_module):
    sql = text("""
    with s as (
        SELECT distinct cst.id_base_site
        FROM gn_monitoring.t_base_sites tbs
        join gn_monitoring.cor_site_type cst
        on tbs.id_base_site = cst.id_base_site
        JOIN gn_monitoring.cor_module_type cmt
        ON cmt.id_type_site = cst.id_type_site
        WHERE cmt.id_module = :id_module
    ), final_data as (
        SELECT tsc.id_base_site , tsc.DATA || jsonb_object_agg(json_key, json_content) as data
        FROM gn_monitoring.t_site_complements tsc
        join s on s.id_base_site = tsc.id_base_site
        CROSS JOIN LATERAL jsonb_each(tsc.data) e(key, value)
        JOIN LATERAL (
            SELECT '_label_' || e.key AS json_key,  string_agg(tn.label_default, '|')   AS json_content
            FROM (
                SELECT e.value #>> '{}' AS id_nomenclature
                WHERE jsonb_typeof(e.value) <> 'array'
                UNION ALL
                SELECT jsonb_array_elements_text(e.value)
                WHERE jsonb_typeof(e.value) = 'array'
            ) v
            JOIN ref_nomenclatures.t_nomenclatures tn
            ON tn.id_nomenclature::text = v.id_nomenclature
        ) lbl ON e.key = ANY(:fields_list)
        GROUP BY  tsc.id_base_site , tsc.data
    )
    update gn_monitoring.t_site_complements tsc
    SET data = final_data.data
    FROM final_data
    WHERE tsc.id_base_site = final_data.id_base_site
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def upgrade_visit(fields_list, id_module):
    sql = text("""
        WITH final_data AS (
            SELECT tvc.id_base_visit , tvc.DATA || jsonb_object_agg(json_key, json_content) as data
            FROM gn_monitoring.t_base_visits tsc
            JOIN gn_monitoring.t_visit_complements tvc
            ON tsc.id_base_visit = tvc.id_base_visit AND tsc.id_module = :id_module
            CROSS JOIN LATERAL jsonb_each(tvc.data) e(jkey, value)
            JOIN LATERAL (
                SELECT '_label_' || e.jkey AS json_key,  string_agg(tn.label_default, '|')   AS json_content
                FROM (
                    SELECT e.value #>> '{}' AS id_nomenclature
                    WHERE jsonb_typeof(e.value) <> 'array'
                    UNION ALL
                    SELECT jsonb_array_elements_text(e.value)
                    WHERE jsonb_typeof(e.value) = 'array'
                ) v
                JOIN ref_nomenclatures.t_nomenclatures tn
                ON tn.id_nomenclature::text = v.id_nomenclature
            ) lbl ON e.jkey = ANY(:fields_list)
            GROUP BY  tvc.id_base_visit , tvc.data
        )
        UPDATE gn_monitoring.t_visit_complements tsc
        SET data = final_data.data
        FROM final_data
        WHERE tsc.id_base_visit = final_data.id_base_visit;
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def upgrade_observation(fields_list, id_module):
    sql = text("""
          with s as (
                SELECT distinct t.id_observation
                FROM gn_monitoring.t_observations t
                join gn_monitoring.t_base_visits tbv
                ON t.id_base_visit = tbv.id_base_visit
                WHERE tbv.id_module = :id_module
        ) , final_data AS (
            SELECT tsc.id_observation  , tsc.DATA || jsonb_object_agg(json_key, json_content) AS data
            FROM gn_monitoring.t_observation_complements tsc
            join s on s.id_observation = tsc.id_observation
            CROSS JOIN LATERAL jsonb_each(tsc.data) e(jkey, value)
            JOIN LATERAL (
                SELECT '_label_' || e.jkey AS json_key,  string_agg(tn.label_default, '|')   AS json_content
                FROM (
                    SELECT e.value #>> '{}' AS id_nomenclature
                    WHERE jsonb_typeof(e.value) <> 'array'
                    UNION ALL
                    SELECT jsonb_array_elements_text(e.value)
                    WHERE jsonb_typeof(e.value) = 'array'
                ) v
                JOIN ref_nomenclatures.t_nomenclatures tn
                ON tn.id_nomenclature::text = v.id_nomenclature
            ) lbl ON e.jkey  = ANY(:fields_list)
            GROUP BY  tsc.id_observation , tsc.data
        )
        UPDATE gn_monitoring.t_observation_complements tsc
        SET data = final_data.data
        FROM final_data
        WHERE tsc.id_observation = final_data.id_observation;
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def upgrade_observation_detail(fields_list, id_module):
    sql = text("""
    with s as (
        SELECT distinct t.id_observation
        FROM gn_monitoring.t_observations t
        join gn_monitoring.t_base_visits tbv
        ON t.id_base_visit = tbv.id_base_visit
        WHERE tbv.id_module = :id_module
    ) , final_data AS (
        SELECT tsc.id_observation_detail  , tsc.DATA || jsonb_object_agg(json_key, json_content) AS data
        FROM gn_monitoring.t_observation_details  tsc
        join s on s.id_observation = tsc.id_observation
        CROSS JOIN LATERAL jsonb_each(tsc.data) e(jkey, value)
        JOIN LATERAL (
            SELECT '_label_' || e.jkey AS json_key,  string_agg(tn.label_default, '|')   AS json_content
            FROM (
                SELECT e.value #>> '{}' AS id_nomenclature
                WHERE jsonb_typeof(e.value) <> 'array'
                UNION ALL
                SELECT jsonb_array_elements_text(e.value)
                WHERE jsonb_typeof(e.value) = 'array'
            ) v
            JOIN ref_nomenclatures.t_nomenclatures tn
            ON tn.id_nomenclature::text = v.id_nomenclature
        ) lbl ON e.jkey  = ANY(:fields_list)
        GROUP BY  tsc.id_observation , tsc.data
    )
    UPDATE gn_monitoring.t_observation_details tsc
    SET data = final_data.data
    FROM final_data
    WHERE tsc.id_observation_detail = final_data.id_observation_detail;
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def upgrade_marking(fields_list, id_module):
    sql = text("""
    with final_data AS (
        SELECT tsc.id_marking , tsc.DATA || jsonb_object_agg(json_key, json_content) AS data
        FROM gn_monitoring.t_marking_events  tsc
        CROSS JOIN LATERAL jsonb_each(tsc.data) e(jkey, value)
        JOIN LATERAL (
            SELECT '_label_' || e.jkey AS json_key,  string_agg(tn.label_default, '|')   AS json_content
            FROM (
                SELECT e.value #>> '{}' AS id_nomenclature
                WHERE jsonb_typeof(e.value) <> 'array'
                UNION ALL
                SELECT jsonb_array_elements_text(e.value)
                WHERE jsonb_typeof(e.value) = 'array'
            ) v
            JOIN ref_nomenclatures.t_nomenclatures tn
            ON tn.id_nomenclature::text = v.id_nomenclature
        ) lbl ON e.jkey  = ANY(:fields_list)
        WHERE tsc.id_module = :id_module
        GROUP BY  tsc.id_marking , tsc.data
    )
    UPDATE gn_monitoring.t_marking_events tsc
    SET data = final_data.data
    FROM final_data
    WHERE tsc.id_marking = final_data.id_marking;
    """).bindparams(fields_list=fields_list, id_module=id_module)
    return sql


def generate_downgrade(table_name):
    sql = text(f"""
        UPDATE gn_monitoring.{table_name}
        SET data = data - ARRAY(
        SELECT k
        FROM jsonb_object_keys(data) AS k
        WHERE left(k, 7) = '_label_'
        );
        """)
    return sql
