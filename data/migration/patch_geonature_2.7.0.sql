-- !!!!!!!!!!!
-- modification à faire si GEONATURE_VERSION >= 2.7.0
-- !!!!!!!!!!!
DROP TRIGGER IF EXISTS tri_meta_dates_change_t_module_complements ON gn_monitoring.t_module_complements;

ALTER TABLE gn_monitoring.t_module_complements DROP meta_create_date;
ALTER TABLE gn_monitoring.t_module_complements DROP meta_update_date;
