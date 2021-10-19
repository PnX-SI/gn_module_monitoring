-- migration 0.2.6 -> 0.2.7


-- ajout d'un colonnne 'gn_monitoring.t_module_complements.b_draw_sites_group' pour l'affichage des groupes de sites

ALTER TABLE gn_monitoring.t_module_complements ADD IF NOT EXISTS b_draw_sites_group BOOLEAN;

