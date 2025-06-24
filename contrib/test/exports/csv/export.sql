
CREATE
OR REPLACE VIEW gn_monitoring.v_export_test_module_sites AS WITH MOD AS (
    SELECT
        *
    FROM
        gn_commons.t_modules AS tm
    WHERE
        module_code = :module_code
)
SELECT
    tbs.base_site_code,
    st_x(tbs.geom) AS longitude,
    st_y(tbs.geom) AS latitude
FROM
    gn_monitoring.t_base_sites AS tbs
    JOIN gn_monitoring.cor_site_module AS csm ON csm.id_base_site = tbs.id_base_site
    AND csm.id_module = (
        SELECT
            id_module
        FROM
            mod
    );


CREATE
OR REPLACE VIEW gn_monitoring.v_export_test_sites AS
SELECT
    tbs.base_site_code,
    st_x(tbs.geom) AS longitude,
    st_y(tbs.geom) AS latitude
FROM
    gn_monitoring.t_base_sites AS tbs
LIMIT 10