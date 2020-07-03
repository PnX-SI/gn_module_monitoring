-- #############################
-- 	Création d'une vue de base
--			pouvant être utilisé dans d'autres modules
--
-- Cette vue regroupe les informations générique des sites est des visites
-- Elle peut servir pour la crétation de vue dans le cadre de la synchronisation avec la synthèse (cf module cheveches).
--
-- #############################
DROP VIEW IF EXISTS gn_monitoring.vs_visits CASCADE;
CREATE VIEW gn_monitoring.vs_visits AS
SELECT
	v.id_module,
	v.uuid_base_visit,
	s.uuid_base_site,
	s.id_base_site,
	v.id_base_visit,
	v.id_dataset,
	id_nomenclature_obs_technique,
	id_nomenclature_grp_typ,
	ref_nomenclatures.get_id_nomenclature('NAT_OBJ_GEO', 'St') AS id_nomenclature_geo_object_nature,
	v.visit_date_min AS date_min,
	COALESCE (v.visit_date_max, v.visit_date_min) AS date_max,
	v.comments AS comment_context,
	s.comments AS site_comment,
	s.geom AS the_geom_4326,
	ST_CENTROID(s.geom) AS the_geom_point,
	s.geom_local as geom_local,
	o.observers,
	o.ids_observers,
	v.id_digitiser
	FROM gn_monitoring.t_base_visits v
	JOIN gn_monitoring.t_base_sites s ON v.id_base_site = s.id_base_site
	LEFT JOIN LATERAL (
		SELECT
			array_agg(r.id_role) AS ids_observers,
			STRING_AGG(CONCAT(r.nom_role, ' ', prenom_role), ' ; ') AS observers
		FROM gn_monitoring.cor_visit_observer cvo
		JOIN utilisateurs.t_roles r
		ON r.id_role = cvo.id_role
		WHERE cvo.id_base_visit = v.id_base_visit
	) o ON true
;

