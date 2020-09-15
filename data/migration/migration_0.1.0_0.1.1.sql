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


