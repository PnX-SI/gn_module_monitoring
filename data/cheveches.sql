-- il est important que le module path corresponde au nom du répertoire dans config/monitorings
INSERT INTO gn_commons.t_modules (
    module_label,
    module_path,
    module_code,
    module_desc,
    active_frontend,
    active_backend,
    module_comment
    )
    VALUES(
        'Chevêches',
        'cheveches',
        'CHEVECHES',
        'Module de suivi des mâles chanteurs de l''espèce Chevêche d''Athéna',
        FALSE,
        FALSE,
        'Sous-module du module monitoring'
    )
;

-- ajout dans la table gn_monitoring.t_module_complements pour signifier que c'est un module de suivi
INSERT INTO gn_monitoring.t_module_complements (
    id_module
    )
    SELECT id_module
        FROM gn_commons.t_modules
        WHERE module_path = 'cheveches'
;

-- cor module data set
INSERT INTO gn_commons.cor_module_dataset (
    id_module,
    id_dataset
    )
    SELECT m.id_module, d.id_dataset
        FROM gn_commons.t_modules m
        JOIN gn_meta.t_datasets d
            ON d.dataset_shortname = 'Cheveches mâles chanteurs'
            WHERE module_path = 'cheveches'
;


-- Nouveaux types
INSERT INTO ref_nomenclatures.bib_nomenclatures_types (id_type, mnemonique, label_default, definition_default, label_fr, definition_fr, source, statut) VALUES
((SELECT max(id_type)+1 FROM ref_nomenclatures.bib_nomenclatures_types), 'CHE_VENT', 'Vent', 'Vent (protocole suivi male chanteur chevêche)', 'Vent', 'Vent (protocole suivi male chanteur chevêche)', 'monitoring_cheveche', 'Validation en cours');

INSERT INTO ref_nomenclatures.bib_nomenclatures_types (id_type, mnemonique, label_default, definition_default, label_fr, definition_fr, source, statut) VALUES
((SELECT max(id_type)+1 FROM ref_nomenclatures.bib_nomenclatures_types), 'CHE_METEO', 'Méteo', 'Méteo (protocole suivi male chanteur chevêche)', 'Méteo', 'Méteo (protocole suivi male chanteur chevêche)', 'monitoring_cheveche', 'Validation en cours');

-- Nomenclatures
INSERT INTO ref_nomenclatures.t_nomenclatures(
	id_type, cd_nomenclature,
	mnemonique, label_default, label_fr,
	source, statut, active
)
VALUES
(ref_nomenclatures.get_id_nomenclature_type('TYPE_SITE'),'CHE_PT_E', 'Pt. É. Chev.','Point d''écoute chevêches','Point d''écoute chevêches','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_VENT'),'CHE_V_FO','Fort','Fort','Fort','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_VENT'),'CHE_V_MO','Modéré','Modéré','Modéré','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_VENT'),'CHE_V_FA','Faible','Faible','Faible','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_VENT'),'CHE_V_NU','Nul','Vent nul','Vent nul','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_METEO'),'CHE_M_NU','Nuageux','Nuageux','Nuageux','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_METEO'),'CHE_M_MNU','Moyennement nuageux','Moyennement nuageux','Moyennement nuageux','monitoring_cheveche','Validation en cours',TRUE),
(ref_nomenclatures.get_id_nomenclature_type('CHE_METEO'),'CHE_M_CL','Clair','Clair','Clair','monitoring_cheveche','Validation en cours',TRUE)
