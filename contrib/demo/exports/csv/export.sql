CREATE OR REPLACE VIEW gn_monitoring.v_export_demo_sites AS
SELECT
    tbs.base_site_code,
    tbs.base_site_name,
    st_x(tbs.geom) AS longitude,
    st_y(tbs.geom) AS latitude
FROM
    gn_monitoring.t_base_sites AS tbs;

CREATE OR REPLACE VIEW gn_monitoring.v_export_demo_obs AS
SELECT
    tv.id_dataset,
    tbs.base_site_code,
    tv.visit_date_min,
    o.cd_nom,
    o.comments
FROM
    gn_monitoring.t_observations AS o
    JOIN gn_monitoring.t_base_visits AS tv ON tv.id_base_visit = o.id_base_visit
    JOIN gn_monitoring.t_base_sites AS tbs ON tbs.id_base_site = tv.id_base_site;
