

-- #############################
-- Insertion de la source
--- permet d'importer les données dans la synthèse
--	 et de les lier au module de saisie
-- EDIT normalement fait à la création du sous module
-- #############################
-- INSERT INTO gn_synthese.t_sources(
--     name_source, 
--     desc_source, 
--     entity_source_pk_field, 
--     url_source
-- )
-- VALUES (
--     'MONITORING_TEST',
--     'Données issues du protocole de test',
--     'gn_monitoring.vs_test.entity_source_pk_value',
--     '#/monitoring/object/test/visit/observation'
-- );


-- #############################
-- 	Création d'une vue 
--		permettant la remonté des données 
--		test dans la synthèse
-- #############################
DROP VIEW IF EXISTS gn_monitoring.vs_test;
CREATE VIEW gn_monitoring.vs_test AS
WITH source AS (
	SELECT id_source 
	FROM gn_synthese.t_sources
	WHERE name_source = 'MONITORING_TEST' -- ici 'MONITORING_<module_path>.upper()'
	LIMIT 1
)
SELECT
		o.uuid_observation AS unique_id_sinp, 
		v.uuid_base_visit AS unique_id_sinp_grp,
		(SELECT id_source FROM source) as id_source,
		o.id_observation AS entity_source_pk_value,
		v.id_dataset,
		v.id_nomenclature_geo_object_nature,
		v.id_nomenclature_grp_typ,
		--id_nomenclature_obs_meth,
		v.id_nomenclature_obs_technique,
		--id_nomenclature_bio_status, 
		--id_nomenclature_bio_condition,
		--id_nomenclature_naturalness,
		--id_nomenclature_exist_proof,-
		--id_nomenclature_valid_status,
		--id_nomenclature_diffusion_level,
		--id_nomenclature_life_stage,
		--id_nomenclature_sex,
 		ref_nomenclatures.get_id_nomenclature('IND', 'OBJ_DENBR') AS id_nomenclature_obj_count,
 		ref_nomenclatures.get_id_nomenclature('TYP_DENBR', 'Es') AS id_nomenclature_type_count,
 		-- id_nomenclature_sensitivity
 		ref_nomenclatures.get_id_nomenclature('STATUT_OBS', 'Pr') AS id_nomenclature_observation_status, 
		-- id_nomenclature_blurring
		ref_nomenclatures.get_id_nomenclature('STATUT_SOURCE', 'Te') AS id_nomenclature_source_status,
		ref_nomenclatures.get_id_nomenclature('TYP_INF_GEO', '1') AS id_nomenclature_info_geo_type,

		1 AS count_min,
		1 AS count_max,
		id_observation,
		o.cd_nom::int AS cd_nom,
		t.nom_complet AS nom_cite,
		--meta_v_taxref
		--sample_number_proof
		--digital_proofvue
		alt.altitude_max,
		v.the_geom_4326,
		v.the_geom_point,
		v.geom_local as the_geom_local,
		v.date_min,
		v.date_max,
		--validator
		--validation_comment
		observers,
		--determiner
		v.id_digitiser,
		--id_nomenclature_determination_method
		--meta_validation_date
		--meta_create_date,
		--meta_update_date,
		--last_action
		v.id_module,
		--comment_context
		v.comment_description,
		ids_observers,
		
		-- ## Colonnes complémentaires pouvant être utile
		v.id_base_site,
		v.id_base_visit
	FROM gn_monitoring.vs_visits v
	JOIN gn_commons.t_modules m ON m.id_module = v.id_module
	--JOIN gn_monitoring.t_visit_complements vc ON vc.id_base_visit = v.id_base_visit
	JOIN gn_monitoring.t_observations o ON o.id_base_visit = v.id_base_visit 
	JOIN taxonomie.taxref t ON t.cd_nom = o.cd_nom
 	LEFT JOIN LATERAL ref_geo.fct_get_altitude_intersection(v.geom_local) alt (altitude_min, altitude_max) ON true
	WHERE m.module_path = 'test';
