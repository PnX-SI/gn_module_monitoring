    CREATE TABLE IF NOT EXISTS gn_monitoring.t_module_complements (
        
        id_module SERIAL NOT NULL,
        uuid_module_complement uuid DEFAULT uuid_generate_v4() NOT NULL,

        CONSTRAINT pk_t_module_complements PRIMARY KEY (id_module),
        CONSTRAINT fk_t_module_complements_id_module FOREIGN KEY (id_module)
            REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
    );


    CREATE TABLE IF NOT EXISTS gn_monitoring.t_site_complements (

        id_base_site INTEGER NOT NULL,
        id_module INTEGER NOT NULL,
        data JSONB,

        CONSTRAINT pk_t_site_complements PRIMARY KEY (id_base_site),
        CONSTRAINT fk_t_site_complements_id_module FOREIGN KEY (id_module)
            REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_t_site_complement_id_base_site FOREIGN KEY (id_base_site)
            REFERENCES gn_monitoring.t_base_sites (id_base_site) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE

    );


    -- on lie la visite au module car le site peut appartenir a plusieurs modules

    ALTER TABLE gn_monitoring.t_base_visits ADD COLUMN IF NOT EXISTS id_module INTEGER NOT NULL;
    ALTER TABLE gn_monitoring.t_base_visits ADD CONSTRAINT fk_t_base_visits_id_module FOREIGN KEY (id_module)
                REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
                ON UPDATE CASCADE ON DELETE CASCADE;



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
        uuid_observation uuid DEFAULT uuid_generate_v4() NOT NULL,


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

