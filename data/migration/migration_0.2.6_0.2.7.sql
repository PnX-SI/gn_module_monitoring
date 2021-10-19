-- migration 0.2.6 -> 0.2.7


-- ajout d'un colonnne 'gn_monitoring.t_module_complements.b_draw_sites_group' pour l'affichage des groupes de sites

ALTER TABLE gn_monitoring.t_module_complements ADD IF NOT EXISTS b_draw_sites_group BOOLEAN;


-- suppression des colonnes meta_create_date et meta_update_date qui font doublons avec gn_commons.t_modules

DROP TRIGGER IF EXISTS tri_meta_dates_change_t_module_complements ON gn_monitoring.t_module_complements;

ALTER TABLE gn_monitoring.t_module_complements DROP IF EXISTS meta_create_date;
ALTER TABLE gn_monitoring.t_module_complements DROP IF EXISTS meta_update_date;
