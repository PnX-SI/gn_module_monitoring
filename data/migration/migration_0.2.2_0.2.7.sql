DROP TRIGGER IF EXISTS tri_meta_dates_change_t_module_complements ON gn_monitoring.t_module_complements;

ALTER TABLE gn_monitoring.t_module_complements DROP IF EXISTS meta_create_date;
ALTER TABLE gn_monitoring.t_module_complements DROP IF EXISTS meta_update_date;
