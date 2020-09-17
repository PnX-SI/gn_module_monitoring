-- mise en base des données de custom.json et choix depuis l'édition du module

ALTER TABLE gn_monitoring.t_module_complements ADD COLUMN id_list_observer INTEGER;

ALTER TABLE gn_monitoring.t_module_complements ADD CONSTRAINT fk_t_module_complements_id_list_observer FOREIGN KEY (id_list_observer)
            REFERENCES utilisateurs.t_listes (id_liste) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE gn_monitoring.t_module_complements ADD COLUMN id_list_taxonomy INTEGER;

ALTER TABLE gn_monitoring.t_module_complements ADD CONSTRAINT fk_t_module_complements_id_list_taxonomy FOREIGN KEY (id_list_taxonomy)
            REFERENCES taxonomie.bib_listes (id_liste) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE gn_monitoring.t_module_complements ADD COLUMN b_synthese BOOLEAN DEFAULT TRUE;
ALTER TABLE gn_monitoring.t_module_complements ADD COLUMN taxonomie_display_field_name CHARACTER VARYING DEFAULT 'nom_vern,lb_nom';


-- create update date for t_modules complements 

ALTER TABLE gn_monitoring.t_module_complements ADD COLUMN meta_create_date timestamp without time zone NOT NULL DEFAULT now();
ALTER TABLE gn_monitoring.t_module_complements ADD COLUMN meta_update_date timestamp without time zone DEFAULT now();


CREATE TRIGGER tri_meta_dates_change_t_medias
          BEFORE INSERT OR UPDATE
          ON gn_monitoring.t_module_complements
          FOR EACH ROW
          EXECUTE PROCEDURE public.fct_trg_meta_dates_change();


-- module_code <- module_path
-- module_path <- <module_monitoring.module_path>/module/module_code>
-- pour être raccord avec les modules classiques sur code et path
-- path permet d'atteindre le module dans le menu de droite sur active_frontend est à true
-- 
-- en sécurité : si module_path contient déjà un '/' -> on ne refait pas l'operation
UPDATE TABLE gn_commons.t_modules m 
    SET 
        module_code = m_submodule.module_code,
        module_path = m_submodule.module_path
SELECT m_submodule.module_path, m_monitoring.module_path||'/module/'||m_submodule.module_code
    FROM gn_commons.t_modules m_submodule
    JOIN gn_monitoring.t_module_complements mc
        ON mc.id_module = m_submodule.id_module
    JOIN gn_commons.t_modules m_monitoring
        ON m_monitoring.module_code = 'MONITORINGS' -- code de monitoring en dur
    WHERE m_submodule.id_module = m.id_module
        AND NOT m_submodule.module_path LIKE '%/%'