
-------------------------------------------------final --POPReptile standard------------------------------------------
-- View: gn_monitoring.v_export_popreptile_standard

DROP  VIEW IF EXISTS gn_monitoring.v_export_popreptile_standard;

CREATE OR REPLACE VIEW gn_monitoring.v_export_popreptile_standard
 AS

SELECT
		aire.id_dataset::text,
		aire.id_sites_group as id_aire,
		aire.nom_aire,
		aire.commune,
		aire.habitat_principal,
		ovs.id as id_point,
		ovs.base_site_code AS numero_point,
		ovs.type_materiaux,
		ovs.saison_prospection,
		ovs.habitat_a,
		ovs.habitat_b,
		ovs.type_milieu_transect,
		ovs.abri_visible,
		ovs.frequentation_humaine,
		ovs.coordonnee_x_lamb93,
		ovs.coordonnee_y_lamb93,
		ovs.id_base_visit AS numero_passage,
		ovs.visit_date_min as date_passage,
		ovs.Heure_debut,
		ovs.Heure_fin,
		ovs.temperature_air,
		ovs.meteo,
		ovs.ensoleillement,
		ovs.vent,
		ovs.pluviosite,
		ovs.espece,
		ovs.stade,
		ovs.sexe,
		ovs.nombre_compte::text,
		ovs.nombre_estime::text
	   FROM ( SELECT s.id_sites_group,
				s.id_base_site as id,
				s.base_site_code,
				s.type_materiaux,
				s.saison_prospection,
				s.habitat_a,
				s.habitat_b,
				s.type_milieu_transect,
				s.abri_visible,
				s.frequentation_humaine,
				s.coordonnee_x_lamb93,
				s.coordonnee_y_lamb93,
				ov.id_base_site,
				ov.id_base_visit,
				ov.visit_date_min,
				ov.Heure_debut,
				ov.Heure_fin,
				ov.temperature_air,
				ov.meteo,
				ov.ensoleillement,
				ov.vent,
				ov.pluviosite,
				ov.id_observation,
				ov.id_base_visit_o,
				ov.stade,
				ov.sexe,
				ov.nombre_compte,
				ov.nombre_estime,
				ov.espece
			   FROM ( SELECT v.id_base_site,
						v.id_base_visit,
						v.visit_date_min,
						v.Heure_debut,
						v.Heure_fin,
						v.temperature_air,
						v.meteo,
						v.ensoleillement,
						v.vent,
						v.pluviosite,
						o.id_observation,
						o.id_base_visit_o,
						o.stade,
						o.sexe,
						o.nombre_compte,
						o.nombre_estime,
						o.espece
					   FROM (
							  SELECT obs.id_observation,
								obs.id_base_visit AS id_base_visit_o,
								n.label_fr AS stade,
								obs.nombre_compte,
								n1.label_fr as nombre_estime,
								replace(obs.sexe::text,'"','') as sexe,
								taxon.lb_nom AS espece
							   FROM (
									SELECT ob.id_observation,
										ob.id_base_visit,
										ob.cd_nom,
										ob.comments,
										ob.uuid_observation,
										oc.data -> 'nombre_compte'::text AS nombre_compte,
										oc.data -> 'nombre_estime'::text AS ne,
										oc.data -> 'id_nomenclature_stade'::text AS st,
										oc.data -> 'sexe'::text AS sexe
									   FROM gn_monitoring.t_observations ob
										 LEFT JOIN gn_monitoring.t_observation_complements oc ON ob.id_observation = oc.id_observation) obs
								 LEFT JOIN taxonomie.taxref taxon ON obs.cd_nom = taxon.cd_nom
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n ON obs.st::character varying::text = n.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON obs.ne::character varying::text = n1.id_nomenclature::character varying::text) o
						 LEFT JOIN (
							   SELECT
								visit.id_base_site,
								visit.id_base_visit,
								visit.visit_date_min,
								Replace(visit.hd::text,'"','') AS Heure_debut,
								Replace(visit.hf::text,'"','') AS Heure_fin,
								visit.ta AS temperature_air,
								n1.label_fr AS meteo,
								n2.label_fr AS ensoleillement,
								n3.label_fr AS vent,
								n4.label_fr AS pluviosite
							   FROM ( SELECT vb.id_base_site,
										vb.id_base_visit,
										vb.visit_date_min,
										vc.data -> 'Heure_debut'::text AS hd,
										vc.data -> 'Heure_fin'::text AS hf,
										vc.data -> 'temperature_air'::text AS ta,
										vc.data -> 'meteo'::text AS mt,
										vc.data -> 'ensoleillement'::text AS es,
										vc.data -> 'vent'::text AS vent,
										vc.data -> 'pluviosite'::text AS pl
									   FROM gn_monitoring.t_base_visits vb
										 LEFT JOIN gn_monitoring.t_visit_complements vc ON vb.id_base_visit = vc.id_base_visit) visit
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON visit.mt::character varying::text = n1.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON visit.es::character varying::text = n2.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON visit.vent::character varying::text = n3.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON visit.pl::character varying::text = n4.id_nomenclature::character varying::text
								 ) v ON o.id_base_visit_o = v.id_base_visit) ov
				 INNER JOIN (
						SELECT
						site.id_sites_group,
						site.id_base_site,
						site.base_site_code,
						n1.label_fr AS type_materiaux,
						n2.label_fr AS saison_prospection,
						n3.label_fr AS habitat_a,
						n4.label_fr AS habitat_b,
						replace(site.tm::text,'"','') AS type_milieu_transect,
						n5.label_fr AS abri_visible,
						n6.label_fr AS frequentation_humaine,
						st_x(ST_Centroid(site.geom)) AS coordonnee_x_lamb93,
						st_y(ST_Centroid(site.geom))AS coordonnee_y_lamb93
					   FROM ( SELECT sc.data -> 'type_materiaux'::text AS tma,
								sc.data -> 'saison_prospection'::text AS sp,
								sc.data -> 'habitat_a'::text AS ha,
								sc.data -> 'habitat_b'::text AS hb,
								sc.data -> 'milieu_transect'::text AS tm,
								sc.data -> 'abri_visible'::text AS av,
								sc.data -> 'frequentation_humaine'::text AS fh,
								sc.id_module,
								sb.id_base_site,
								sb.id_inventor,
								sb.id_digitiser,
								sb.id_nomenclature_type_site,
								sb.base_site_name,
								sb.base_site_description,
								sb.base_site_code,
								sb.first_use_date,
								sb.geom,
								sb.geom_local,
								sb.altitude_min,
								sb.altitude_max,
								sb.uuid_base_site,
								sb.meta_create_date,
								sb.meta_update_date,
								sc.id_sites_group
							   FROM gn_monitoring.t_base_sites sb
							   LEFT JOIN gn_monitoring.t_site_complements sc ON sb.id_base_site = sc.id_base_site) site
						 INNER JOIN (select id_module, module_code from  gn_commons.t_modules WHERE lower(module_code)='popreptile') m ON site.id_module::character varying::text = m.id_module::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON site.tma::character varying::text = n1.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON site.sp::character varying::text = n2.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON site.ha::character varying::text = n3.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON site.hb::character varying::text = n4.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON site.av::character varying::text = n5.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON site.fh::character varying::text = n6.id_nomenclature::character varying::text
						) s ON s.id_base_site = ov.id_base_site) ovs

		 LEFT JOIN (
			   SELECT
			   a.id_dataset,
			   a.id_sites_group,
				a.sites_group_name AS nom_aire,
				c.nom_com AS commune,
				h.search_name AS habitat_principal
			   FROM ( SELECT
						t_sites_groups.id_sites_group,
						t_sites_groups.sites_group_name,
						(t_sites_groups.data -> 'commune'::text) ->> 0 AS commune,
						t_sites_groups.data -> 'habitat_principal'::text AS hp,
						t_sites_groups.data -> 'id_dataset'::text AS id_dataset
					   FROM gn_monitoring.t_sites_groups) a
				 LEFT JOIN ref_habitats.autocomplete_habitat h ON a.hp::text = h.cd_hab::text
				 LEFT JOIN ref_geo.li_municipalities c ON a.commune::character varying::text = c.insee_com::text) aire ON aire.id_sites_group = ovs.id_sites_group;



------------------------------------------------finale --POPReptile analyses------------------------------------------
-- View: gn_monitoring.v_export_popreptile_analyse

DROP VIEW IF EXISTS gn_monitoring.v_export_popreptile_analyses;

CREATE OR REPLACE VIEW gn_monitoring.v_export_popreptile_analyses
 AS

SELECT
		aire.id_dataset::text,
		aire.id_sites_group as id_aire,
		aire.nom_aire,
		aire.commune,
		aire.habitat_principal,
		ovs.id as id_point,
		ovs.base_site_code AS numero_point,
		ovs.coordonnee_x_lamb93,
		ovs.coordonnee_y_lamb93,
		ovs.num_passage AS numero_passage,
		ovs.visit_date_min as date_passage,
		ovs.espece as espece,
		--case when ovs.observe is not null then ovs.observe else 0 end as observe,
		ovs.stade,
		ovs.sexe,
		ovs.comments as remarques

	   FROM ( SELECT s.id_sites_group,
				s.id_base_site as id,
				s.base_site_code,
				s.coordonnee_x_lamb93,
				s.coordonnee_y_lamb93,
				ov.id_base_site,
				ov.id_base_visit,
				ov.visit_date_min,
				ov.id_observation,
				ov.id_base_visit_o,
				ov.stade,
				ov.sexe,
				ov.espece,
				--ov.observe,
				ov.comments,
				ov.num_passage
				--ov.espece_p
			   FROM ( SELECT
						v.id_base_site,
						v.id_base_visit,
						v.visit_date_min,
						v.num_passage,
						o.id_observation,
						o.id_base_visit_o,
						o.stade,
						o.sexe,
						o.espece,
						--o.observe,
						o.comments
						--v.espece_p
					   FROM (
							SELECT obs.id_observation,
								obs.id_base_visit AS id_base_visit_o,
								n.label_fr AS stade,
								replace(obs.sexe::text,'"','') as sexe,
								taxon.lb_nom AS espece,
								obs.comments
							   FROM (
									SELECT ob.id_observation,
										ob.id_base_visit,
										ob.cd_nom,
										ob.comments,
										ob.uuid_observation,
										oc.data -> 'id_nomenclature_stade'::text AS st,
										oc.data -> 'sexe'::text AS sexe
									   FROM gn_monitoring.t_observations ob
										 LEFT JOIN gn_monitoring.t_observation_complements oc ON ob.id_observation = oc.id_observation
									) obs
									LEFT JOIN taxonomie.taxref taxon ON obs.cd_nom = taxon.cd_nom
									LEFT JOIN ref_nomenclatures.t_nomenclatures n ON obs.st::character varying::text = n.id_nomenclature::character varying::text
							) o
						LEFT JOIN (
									SELECT
										visit.id_base_site,
										visit.id_base_visit,
										visit.visit_date_min,
										visit.num_passage
									FROM ( SELECT vb.id_base_site,
												vb.id_base_visit,
												vb.visit_date_min,
												vc.data -> 'num_passage'::text AS num_passage
											   FROM gn_monitoring.t_base_visits vb
												 LEFT JOIN gn_monitoring.t_visit_complements vc ON vb.id_base_visit = vc.id_base_visit) visit

								 ) v
						ON o.id_base_visit_o = v.id_base_visit
					) ov
				 INNER JOIN (
						SELECT
						site.id_sites_group,
						site.id_base_site,
						site.base_site_code,
						st_x(ST_Centroid(site.geom)) AS coordonnee_x_lamb93,
						st_y(ST_Centroid(site.geom))AS coordonnee_y_lamb93
					   FROM ( SELECT
								sc.id_module,
								sb.id_base_site,
								sb.id_inventor,
								sb.id_digitiser,
								sb.id_nomenclature_type_site,
								sb.base_site_name,
								sb.base_site_description,
								sb.base_site_code,
								sb.first_use_date,
								sb.geom,
								sb.geom_local,
								sb.altitude_min,
								sb.altitude_max,
								sb.uuid_base_site,
								sb.meta_create_date,
								sb.meta_update_date,
								sc.id_sites_group
							   FROM gn_monitoring.t_base_sites sb
							   LEFT JOIN gn_monitoring.t_site_complements sc ON sb.id_base_site = sc.id_base_site) site
						 INNER JOIN (select id_module, module_code from  gn_commons.t_modules WHERE lower(module_code)='popreptile') m ON site.id_module::character varying::text = m.id_module::character varying::text
						) s ON s.id_base_site = ov.id_base_site) ovs

		 LEFT JOIN (
			   SELECT
			    a.id_dataset,
				a.id_sites_group,
				a.sites_group_name AS nom_aire,
				c.nom_com AS commune,
				h.search_name AS habitat_principal
			   FROM ( SELECT
						t_sites_groups.id_sites_group,
						t_sites_groups.sites_group_name,
						(t_sites_groups.data -> 'commune'::text) ->> 0 AS commune,
						t_sites_groups.data -> 'habitat_principal'::text AS hp,
						t_sites_groups.data -> 'id_dataset'::text AS id_dataset
					   FROM gn_monitoring.t_sites_groups) a
				 LEFT JOIN ref_habitats.autocomplete_habitat h ON a.hp::text = h.cd_hab::text
				 LEFT JOIN ref_geo.li_municipalities c ON a.commune::character varying::text = c.insee_com::text) aire ON aire.id_sites_group = ovs.id_sites_group

order by (aire.id_sites_group, ovs.base_site_code, ovs.id_base_visit)	;


-------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------





