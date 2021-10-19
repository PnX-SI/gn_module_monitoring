 alter table gn_monitoring.t_base_sites alter column id_nomenclature_type_site drop not null;

-------------------------------------------------final --POPAmphibien standard------------------------------------------
-- View: gn_monitoring.v_export_popamphibien_standard

DROP VIEW  IF EXISTS  gn_monitoring.v_export_popamphibien_standard;

CREATE OR REPLACE VIEW gn_monitoring.v_export_popamphibien_standard
 AS

SELECT
		aire.id_dataset::text,
		aire.id_sites_group as id_aire,
		aire.nom_aire,
		aire.commune,
		aire.categories_paysageres,
		ovs.id as id_site,
		ovs.base_site_code AS numero_site,
		ovs.coordonnee_x as coordonnee_x_lamb93,
		ovs.coordonnee_y as coordonnee_y_lamb93,
		ovs.milieu_aquatique,
		ovs.turbidite,
		ovs.variation_eau,
		ovs.courant,
		ovs.vegetation_aquatique_principale,
		ovs.rives,
		ovs.habitat_terrestre_environnant,
		ovs.activite_humaine,
		ovs.site_protege,
		ovs.id_base_visit AS numero_passage,
		ovs.visit_date_min as date_passage,
		ovs.temperature_air,
		ovs.temperature_eau,
		ovs.ensoleillement,
		ovs.vent,
		ovs.pluviosite,
		ovs.methode_de_prospection,
		ovs.espece,
		ovs.stade,
		ovs.nombre_compte,
		ovs.nombre_estime
	   FROM ( SELECT s.id_sites_group,
				s.id_base_site as id,
				s.base_site_code,
				s.coordonnee_x,
				s.coordonnee_y,
				s.milieu_aquatique,
				s.turbidite,
				s.variation_eau,
				s.courant,
				s.vegetation_aquatique_principale,
				s.rives,
				s.habitat_terrestre_environnant,
				s.activite_humaine,
				s.site_protege,
				ov.id_base_site,
				ov.id_base_visit,
				ov.visit_date_min,
				ov.temperature_air,
				ov.temperature_eau,
				ov.ensoleillement,
				ov.vent,
				ov.pluviosite,
				ov.methode_de_prospection,
				ov.id_observation,
				ov.id_base_visit_o,
				ov.stade,
				ov.nombre_compte,
				ov.nombre_estime,
				ov.espece
			   FROM ( SELECT v.id_base_site,
						v.id_base_visit,
						v.visit_date_min,
						v.temperature_air,
						v.temperature_eau,
						v.ensoleillement,
						v.vent,
						v.pluviosite,
						v.methode_de_prospection,
						o.id_observation,
						o.id_base_visit_o,
						o.stade,
						o.nombre_compte,
						o.nombre_estime,
						o.espece
					   FROM ( SELECT obs.id_observation,
								obs.id_base_visit AS id_base_visit_o,
								n.label_fr AS stade,
								obs.nombre_compte,
								n1.label_fr as nombre_estime,
								taxon.lb_nom AS espece
							   FROM ( SELECT ob.id_observation,
										ob.id_base_visit,
										ob.cd_nom,
										ob.comments,
										ob.uuid_observation,
										oc.data -> 'nombre_compte'::text AS nombre_compte,
										oc.data -> 'nombre_estime'::text AS ne,
										oc.data -> 'id_nomenclature_stade'::text AS st
									   FROM gn_monitoring.t_observations ob
										 LEFT JOIN gn_monitoring.t_observation_complements oc ON ob.id_observation = oc.id_observation) obs
								 LEFT JOIN taxonomie.taxref taxon ON obs.cd_nom = taxon.cd_nom
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n ON obs.st::character varying::text = n.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON obs.ne::character varying::text = n1.id_nomenclature::character varying::text) o
						 LEFT JOIN ( SELECT
								visit.id_base_site,
								visit.id_base_visit,
								visit.visit_date_min,
								visit.ta AS temperature_air,
								visit.te AS temperature_eau,
								n3.label_fr AS ensoleillement,
								n4.label_fr AS vent,
								n5.label_fr AS pluviosite,
								n6.label_fr AS methode_de_prospection
							   FROM ( SELECT vb.id_base_site,
										vb.id_base_visit,
										vb.visit_date_min,
										vc.data -> 'temperature_air'::text AS ta,
										vc.data -> 'temperature_eau'::text AS te,
										vc.data -> 'ensoleillement'::text AS en,
										vc.data -> 'vent'::text AS vent,
										vc.data -> 'pluviosite'::text AS pl,
										vc.data -> 'methode_de_prospection'::text AS mp
									   FROM gn_monitoring.t_base_visits vb
										 LEFT JOIN gn_monitoring.t_visit_complements vc ON vb.id_base_visit = vc.id_base_visit) visit
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON visit.en::character varying::text = n3.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON visit.vent::character varying::text = n4.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON visit.pl::character varying::text = n5.id_nomenclature::character varying::text
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON visit.mp::character varying::text = n6.id_nomenclature::character varying::text) v ON o.id_base_visit_o = v.id_base_visit) ov
				 INNER JOIN ( SELECT
						site.id_sites_group,
						site.id_base_site,
						site.base_site_code,
						st_x(ST_Centroid(site.geom)) AS coordonnee_x,
						st_y(ST_Centroid(site.geom))AS coordonnee_y,
						n1.label_fr AS milieu_aquatique,
						n2.label_fr AS turbidite,
						n3.label_fr AS variation_eau,
						n4.label_fr AS courant,
						n5.label_fr AS vegetation_aquatique_principale,
						n6.label_fr AS rives,
						n7.label_fr AS habitat_terrestre_environnant,
						n8.label_fr AS activite_humaine,
						n9.label_fr AS site_protege
					   FROM ( SELECT sc.data -> 'milieu_aquatique'::text AS ma,
								sc.data -> 'turbidite'::text AS turb,
								sc.data -> 'variation_eau'::text AS ve,
								sc.data -> 'courant'::text AS courant,
								sc.data -> 'vegetation_aquatique_principale'::text AS vap,
								sc.data -> 'rives'::text AS riv,
								sc.data -> 'habitat_terrestre_environnant'::text AS hab_ter,
								sc.data -> 'activite_humaine'::text AS actv,
								sc.data -> 'site_protege_oui'::text AS sp,
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
						 INNER JOIN (select id_module, module_code from  gn_commons.t_modules WHERE lower(module_code)='popamphibien') m ON site.id_module::character varying::text = m.id_module::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON site.ma::character varying::text = n1.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON site.turb::character varying::text = n2.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON site.ve::character varying::text = n3.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON site.courant::character varying::text = n4.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON site.vap::character varying::text = n5.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON site.riv::character varying::text = n6.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n7 ON site.hab_ter::character varying::text = n7.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n8 ON site.actv::character varying::text = n8.id_nomenclature::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n9 ON site.sp::character varying::text = n9.id_nomenclature::character varying::text) s ON s.id_base_site = ov.id_base_site) ovs

		 LEFT JOIN ( SELECT
				a.id_dataset,
				a.id_sites_group,
				a.sites_group_name AS nom_aire,
				c.nom_com AS commune,
				n.label_fr AS categories_paysageres
			   FROM ( SELECT t_sites_groups.id_sites_group,
						t_sites_groups.sites_group_name,
						(t_sites_groups.data -> 'commune'::text) ->> 0 AS commune,
						t_sites_groups.data -> 'categories_paysageres'::text AS cp,
						t_sites_groups.data -> 'id_dataset'::text AS id_dataset
					   FROM gn_monitoring.t_sites_groups ) a
				 LEFT JOIN ref_nomenclatures.t_nomenclatures n ON a.cp::text = n.id_nomenclature::text
				 LEFT JOIN ref_geo.li_municipalities c ON a.commune::character varying::text = c.insee_com::text) aire ON aire.id_sites_group = ovs.id_sites_group;








------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
--					VERSION					17/02/2021
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------

-- View: gn_monitoring.v_export_popamphibien_analyses

DROP VIEW IF EXISTS gn_monitoring.v_export_popamphibien_analyses;

CREATE OR REPLACE VIEW gn_monitoring.v_export_popamphibien_analyses
 AS

SELECT
		aire.id_dataset::text,
		aire.id_sites_group as id_aire,
		aire.nom_aire,
		aire.commune,
		aire.categories_paysageres,
		ovs.id as id_site,
		ovs.base_site_name AS nom_site,
		ovs.coordonnee_x as coordonnee_x_lamb93,
		ovs.coordonnee_y as coordonnee_y_lamb93,
		ovs.milieu_aquatique,
		ovs.num_passage AS numero_passage,
		ovs.visit_date_min as date_passage,
		ovs.presence_poisson::text,
		ovs.espece ,
		--case when ovs.observe is not null then ovs.observe else 0 end as observe,
		ovs.stade,
		ovs.comments as remarques


	   FROM ( SELECT
				s.id_sites_group,
				s.id_base_site as id,
				s.base_site_name,
				s.coordonnee_x,
				s.coordonnee_y,
				s.milieu_aquatique,
				ov.id_base_site,
				ov.id_base_visit,
				ov.visit_date_min,
				ov.presence_poisson,
				ov.id_observation,
				ov.id_base_visit_o,
				ov.stade,
				ov.espece  ,
				--ov.observe,
				ov.comments,
				ov.num_passage
			    --ov.espece_p

			   FROM ( SELECT

						v.id_base_site,
						v.id_base_visit,
						v.visit_date_min,
						v.presence_poisson,
						o.id_observation,
						o.id_base_visit_o,
						o.espece,
						--o.observe,
						o.stade,
						o.comments,
						v.num_passage
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
										 LEFT JOIN gn_monitoring.t_observation_complements oc ON ob.id_observation = oc.id_observation) obs
								 LEFT JOIN taxonomie.taxref taxon ON obs.cd_nom = taxon.cd_nom
								 LEFT JOIN ref_nomenclatures.t_nomenclatures n ON obs.st::character varying::text = n.id_nomenclature::character varying::text
								 ) o
						 LEFT JOIN (
								   SELECT
									visit.id_base_site,
									visit.id_base_visit,
									visit.visit_date_min,
									visit.presence_poisson,
									visit.num_passage
									   FROM (  SELECT vb.id_base_site,
													vb.id_base_visit,
													vb.visit_date_min,
													vc.data -> 'presence_poisson'::text AS presence_poisson,
													vc.data -> 'num_passage'::text AS num_passage
											   FROM gn_monitoring.t_base_visits vb
											   LEFT JOIN gn_monitoring.t_visit_complements vc ON vb.id_base_visit = vc.id_base_visit) visit

								 ) v ON o.id_base_visit_o = v.id_base_visit) ov
				 INNER JOIN ( SELECT
						site.id_sites_group,
						site.id_base_site,
						site.base_site_name,
						st_x(ST_Centroid(site.geom)) AS coordonnee_x,
						st_y(ST_Centroid(site.geom))AS coordonnee_y,
						n1.label_fr AS milieu_aquatique

					   FROM ( SELECT
								sc.data -> 'milieu_aquatique'::text AS ma,

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
						 INNER JOIN (select id_module, module_code from  gn_commons.t_modules WHERE lower(module_code)='popamphibien') m ON site.id_module::character varying::text = m.id_module::character varying::text
						 LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON site.ma::character varying::text = n1.id_nomenclature::character varying::text
						 ) s ON s.id_base_site = ov.id_base_site) ovs

		 LEFT JOIN ( SELECT
				a.id_dataset,
				a.id_sites_group,
				a.sites_group_name AS nom_aire,
				c.nom_com AS commune,
				n.label_fr AS categories_paysageres
			   FROM ( SELECT t_sites_groups.id_sites_group,
						t_sites_groups.sites_group_name,
						(t_sites_groups.data -> 'commune'::text) ->> 0 AS commune,
						t_sites_groups.data -> 'categories_paysageres'::text AS cp,
						t_sites_groups.data -> 'id_dataset'::text AS id_dataset
					   FROM gn_monitoring.t_sites_groups) a
				 LEFT JOIN ref_nomenclatures.t_nomenclatures n ON a.cp::text = n.id_nomenclature::text
				 LEFT JOIN ref_geo.li_municipalities c ON a.commune::character varying::text = c.insee_com::text) aire ON aire.id_sites_group = ovs.id_sites_group
order by (aire.id_sites_group,ovs.id, ovs.id_base_visit);

