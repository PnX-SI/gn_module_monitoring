-- le fichier sera joué à l'installation avec la valeur de module_code qui sera attribué automatiquement
--
--
-- Personalisations possibles
--
--  - ajouter des champs specifiques qui peuvent alimenter la synthese
--      jointure avec les table de complement
--
--  - choisir les valeurs de champs de nomenclatures qui seront propres au modules


-- ce fichier contient une variable :module_code (ou :'module_code')
-- utiliser psql avec l'option -v module_code=<module_code

-- ne pas remplacer cette variable, elle est indispensable pour les scripts d'installations
-- le module pouvant être installé avec un code différent de l'original

DROP VIEW IF EXISTS gn_monitoring.v_synthese_POPReptile;
CREATE OR REPLACE VIEW gn_monitoring.v_synthese_POPReptile
 AS
 WITH source AS (
         SELECT t_sources.id_source
           FROM gn_synthese.t_sources
          WHERE t_sources.name_source::text = concat('MONITORING_', upper('POPReptile'::text))
         LIMIT 1
        ), sites AS (
         SELECT t_base_sites.id_base_site,
            t_base_sites.geom AS the_geom_4326,
            st_centroid(t_base_sites.geom) AS the_geom_point,
            t_base_sites.geom_local
           FROM gn_monitoring.t_base_sites
        ), visits AS (
         SELECT t_base_visits.id_base_visit,
            t_base_visits.uuid_base_visit,
            t_base_visits.id_module,
            t_base_visits.id_base_site,
            t_base_visits.id_dataset,
            t_base_visits.id_digitiser,
            t_base_visits.visit_date_min AS date_min,
            COALESCE(t_base_visits.visit_date_max, t_base_visits.visit_date_min) AS date_max,
            t_base_visits.comments,
            t_base_visits.id_nomenclature_tech_collect_campanule,
            t_base_visits.id_nomenclature_grp_typ
           FROM gn_monitoring.t_base_visits
        ), observers AS (
         SELECT array_agg(r.id_role) AS ids_observers,
            string_agg(concat(r.nom_role, ' ', r.prenom_role), ' ; '::text) AS observers,
            cvo.id_base_visit
           FROM gn_monitoring.cor_visit_observer cvo
             JOIN utilisateurs.t_roles r ON r.id_role = cvo.id_role
          GROUP BY cvo.id_base_visit
        )
 SELECT o.uuid_observation AS unique_id_sinp,
    v.uuid_base_visit AS unique_id_sinp_grp,
    source.id_source,
    o.id_observation AS entity_source_pk_value,
    v.id_dataset,
    ref_nomenclatures.get_id_nomenclature('NAT_OBJ_GEO'::character varying, 'St'::character varying) AS id_nomenclature_geo_object_nature,
    v.id_nomenclature_grp_typ,
    v.id_nomenclature_tech_collect_campanule,
    ref_nomenclatures.get_id_nomenclature('IND'::character varying, 'OBJ_DENBR'::character varying) AS id_nomenclature_obj_count,
    ref_nomenclatures.get_id_nomenclature('TYP_DENBR'::character varying, 'Es'::character varying) AS id_nomenclature_type_count,
    ref_nomenclatures.get_id_nomenclature('STATUT_OBS'::character varying, 'Pr'::character varying) AS id_nomenclature_observation_status,
    ref_nomenclatures.get_id_nomenclature('STATUT_SOURCE'::character varying, 'Te'::character varying) AS id_nomenclature_source_status,
    ref_nomenclatures.get_id_nomenclature('TYP_INF_GEO'::character varying, '1'::character varying) AS id_nomenclature_info_geo_type,
    1 AS count_min,
    1 AS count_max,
    o.id_observation,
    o.cd_nom,
    t.nom_complet AS nom_cite,
    alt.altitude_min,
    alt.altitude_max,
    s.the_geom_4326,
    s.the_geom_point,
    s.geom_local AS the_geom_local,
    v.date_min,
    v.date_max,
    obs.observers,
    v.id_digitiser,
    v.id_module,
    v.comments AS comment_context,
    o.comments AS comment_description,
    obs.ids_observers,
    v.id_base_site,
    v.id_base_visit
   FROM gn_monitoring.t_observations o
     JOIN visits v ON v.id_base_visit = o.id_base_visit
     JOIN sites s ON s.id_base_site = v.id_base_site
     JOIN gn_commons.t_modules m ON m.id_module = v.id_module
     JOIN taxonomie.taxref t ON t.cd_nom = o.cd_nom
     JOIN source ON true
     JOIN observers obs ON obs.id_base_visit = v.id_base_visit
     LEFT JOIN LATERAL ref_geo.fct_get_altitude_intersection(s.geom_local) alt(altitude_min, altitude_max) ON true
  WHERE m.module_code::text = 'POPReptile'::text;

ALTER TABLE gn_monitoring.v_synthese_POPReptile
    OWNER TO geonatadmin;

