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
;

-- group site

  -- creation gn_monitoring.t_group_site

CREATE TABLE IF NOT EXISTS gn_monitoring.t_group_sites (
    id_group_site SERIAL NOT NULL,

    id_module INTEGER NOT NULL,
    group_site_name character varying(255),
    group_site_code character varying(255),
    group_site_description TEXT,
    uuid_group_site UUID DEFAULT uuid_generate_v4() NOT NULL,
    comment TEXT,
    data JSONB,
    meta_create_date timestamp without time zone DEFAULT now(),
    meta_update_date timestamp without time zone DEFAULT now(),

    CONSTRAINT pk_t_group_sites PRIMARY KEY (id_group_site),
    CONSTRAINT fk_t_group_sites_id_module FOREIGN KEY (id_module)
        REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TRIGGER tri_meta_dates_change_t_group_sites
    BEFORE INSERT OR UPDATE
    ON gn_monitoring.t_group_sites
    FOR EACH ROW
    EXECUTE PROCEDURE public.fct_trg_meta_dates_change();


  -- ajout id_group_site à gn_monitoring.t_site_complements

ALTER TABLE gn_monitoring.t_site_complements ADD id_group_site INTEGER;
ALTER TABLE gn_monitoring.t_site_complements ADD CONSTRAINT
    fk_t_site_complement_id_group_site FOREIGN KEY (id_group_site)
    REFERENCES gn_monitoring.t_group_sites (id_group_site) MATCH SIMPLE
    ON UPDATE CASCADE ON DELETE SET NULL;

-- pour ajout de group site et au cas où il en manquerait
INSERT INTO gn_commons.bib_tables_location(table_desc, schema_name, table_name, pk_field, uuid_field_name)
VALUES
('Table centralisant les modules faisant l''objet de protocole de suivis', 'gn_monitoring', 't_module_complements', 'id_module', 'uuid_module_complement'),
('Table centralisant les observations réalisées lors d''une visite sur un site', 'gn_monitoring', 't_observations', 'id_observation', 'uuid_observation'),
('Table centralisant les sites faisant l''objet de protocole de suivis', 'gn_monitoring', 't_base_sites', 'id_base_site', 'uuid_base_site'),
('Table centralisant les groupes de sites faisant l''objet de protocole de suivis', 'gn_monitoring', 't_group_sites', 'id_group_site', 'uuid_group_site'),
('Table centralisant les visites réalisées sur un site', 'gn_monitoring', 't_base_visits', 'id_base_visit', 'uuid_base_visit')
-- on evite de mettre 2 fois le meme couple (shema_name, table_name)
ON CONFLICT(schema_name, table_name) DO NOTHING;
