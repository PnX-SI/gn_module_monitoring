-- schema qui complete gn_monitoring pour le module monitoring

CREATE TABLE IF NOT EXISTS gn_monitoring.t_module_complements (

        id_module SERIAL NOT NULL,
        uuid_module_complement UUID DEFAULT uuid_generate_v4() NOT NULL,

        id_list_observer INTEGER,
        id_list_taxonomy INTEGER,
        b_synthese BOOLEAN DEFAULT TRUE,
        taxonomy_display_field_name CHARACTER VARYING DEFAULT 'nom_vern,lb_nom',
        b_draw_sites_group BOOLEAN,

        data JSONB,

        CONSTRAINT pk_t_module_complements PRIMARY KEY (id_module),
        CONSTRAINT fk_t_module_complements_id_module FOREIGN KEY (id_module)
            REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_t_module_complements_id_list_observer FOREIGN KEY (id_list_observer)
            REFERENCES utilisateurs.t_listes (id_liste) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_t_module_complements_id_list_taxonomy FOREIGN KEY (id_list_taxonomy)
            REFERENCES taxonomie.bib_listes (id_liste) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    -- Les groupes de site

    CREATE TABLE IF NOT EXISTS gn_monitoring.t_sites_groups (
        id_sites_group SERIAL NOT NULL,

        id_module INTEGER NOT NULL,
        sites_group_name character varying(255),
        sites_group_code character varying(255),
        sites_group_description TEXT,
        uuid_sites_group UUID DEFAULT uuid_generate_v4() NOT NULL,
        comments TEXT,
        data JSONB,
        meta_create_date timestamp without time zone DEFAULT now(),
        meta_update_date timestamp without time zone DEFAULT now(),

        CONSTRAINT pk_t_sites_groups PRIMARY KEY (id_sites_group),
        CONSTRAINT fk_t_sites_groups_id_module FOREIGN KEY (id_module)
            REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    DROP TRIGGER IF EXISTS tri_meta_dates_change_t_sites_groups ON gn_monitoring.t_sites_groups;
    CREATE TRIGGER tri_meta_dates_change_t_sites_groups
        BEFORE INSERT OR UPDATE
        ON gn_monitoring.t_sites_groups
        FOR EACH ROW
        EXECUTE PROCEDURE public.fct_trg_meta_dates_change();

    CREATE TABLE IF NOT EXISTS gn_monitoring.t_site_complements (

        id_base_site INTEGER NOT NULL,
        id_module INTEGER NOT NULL,
        id_sites_group INTEGER,
        data JSONB,

        CONSTRAINT pk_t_site_complements PRIMARY KEY (id_base_site),
        CONSTRAINT fk_t_site_complements_id_module FOREIGN KEY (id_module)
            REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_t_site_complement_id_base_site FOREIGN KEY (id_base_site)
            REFERENCES gn_monitoring.t_base_sites (id_base_site) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_t_site_complement_id_sites_group FOREIGN KEY (id_sites_group)
            REFERENCES gn_monitoring.t_sites_groups (id_sites_group) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE SET NULL -- on ne supprime pas forcement les sites quand on supprime un groupe ??

    );

    CREATE TABLE IF NOT EXISTS gn_monitoring.t_visit_complements (

        id_base_visit INTEGER NOT NULL,
        data JSONB,

        CONSTRAINT pk_t_visit_complements PRIMARY KEY (id_base_visit),
        CONSTRAINT fk_t_visit_complements_id_base_visit FOREIGN KEY (id_base_visit)
            REFERENCES gn_monitoring.t_base_visits (id_base_visit) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );


    CREATE TABLE IF NOT EXISTS gn_monitoring.t_observations (
        id_observation SERIAL NOT NULL,
        id_base_visit INTEGER NOT NULL,
        cd_nom INTEGER NOT NULL,
        comments TEXT,
        uuid_observation UUID DEFAULT uuid_generate_v4() NOT NULL,


        CONSTRAINT pk_t_observations PRIMARY KEY (id_observation),
        CONSTRAINT fk_t_observations_id_base_visit FOREIGN KEY (id_base_visit)
            REFERENCES gn_monitoring.t_base_visits (id_base_visit) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );


    -- champs en complément de t_observation: relation 1-1

    CREATE TABLE IF NOT EXISTS gn_monitoring.t_observation_complements (

        id_observation INTEGER NOT NULL,
        data JSONB,

        CONSTRAINT pk_t_observation_complements PRIMARY KEY (id_observation),
        CONSTRAINT fk_t_observation_complements_id_observation FOREIGN KEY (id_observation)
            REFERENCES gn_monitoring.t_observations (id_observation) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    -- table fille de t_observation relation 1-n

    CREATE TABLE IF NOT EXISTS gn_monitoring.t_observation_details (

        id_observation_detail SERIAL NOT NULL,
        id_observation INTEGER NOT NULL,
        data JSONB,

        CONSTRAINT pk_t_observation_details PRIMARY KEY (id_observation),
        CONSTRAINT fk_t_observation_details_id_observation FOREIGN KEY (id_observation)
            REFERENCES gn_monitoring.t_observations (id_observation) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );


    -- pour ne pas remettre des lignes qui existent déjà

    INSERT INTO gn_commons.bib_tables_location(table_desc, schema_name, table_name, pk_field, uuid_field_name)
    VALUES
    ('Table centralisant les modules faisant l''objet de protocole de suivis', 'gn_monitoring', 't_module_complements', 'id_module', 'uuid_module_complement'),
    ('Table centralisant les observations réalisées lors d''une visite sur un site', 'gn_monitoring', 't_observations', 'id_observation', 'uuid_observation'),
    ('Table centralisant les sites faisant l''objet de protocole de suivis', 'gn_monitoring', 't_base_sites', 'id_base_site', 'uuid_base_site'),
    ('Table centralisant les groupes de sites faisant l''objet de protocole de suivis', 'gn_monitoring', 't_sites_groups', 'id_sites_group', 'uuid_sites_group'),
    ('Table centralisant les visites réalisées sur un site', 'gn_monitoring', 't_base_visits', 'id_base_visit', 'uuid_base_visit')
    -- on evite de mettre 2 fois le meme couple (shema_name, table_name)
    ON CONFLICT(schema_name, table_name) DO NOTHING;


INSERT INTO gn_permissions.t_objects (code_object, description_object)
VALUES
('GNM_SITES', 'Permissions sur les sites'),
('GNM_VISITES', 'Permissions sur les visites'),
('GNM_OBSERVATIONS', 'Permissions sur les observation'),
('GNM_GRP_SITES', 'Permissions sur les groupes de sites')
    ON CONFLICT(code_object) DO NOTHING;
