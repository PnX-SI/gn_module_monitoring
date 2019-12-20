ALTER TABLE gn_monitoring.t_base_visits ADD id_dataset integer NOT NULL;

ALTER TABLE gn_monitoring.t_base_visits ADD CONSTRAINT fk_t_base_visits_t_datasets FOREIGN KEY (id_dataset)
      REFERENCES gn_meta.t_datasets (id_dataset) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE NO ACTION;

ALTER TABLE gn_monitoring.t_module_informations ADD id_dataset integer NOT NULL;

ALTER TABLE gn_monitoring.t_module_informations ADD CONSTRAINT fk_t_monitorings_t_datasets FOREIGN KEY (id_dataset)
      REFERENCES gn_meta.t_datasets (id_dataset) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE NO ACTION;

--Created here because gn_meta uses gn_commons (see above) and must be created after gn_commons
CREATE TABLE gn_commons.cor_module_dataset (
    id_module integer NOT NULL,
    id_dataset integer NOT NULL,
  CONSTRAINT pk_cor_module_dataset PRIMARY KEY (id_module, id_dataset),
  CONSTRAINT fk_cor_module_dataset_id_module FOREIGN KEY (id_module)
      REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE NO ACTION,
  CONSTRAINT fk_cor_module_dataset_id_dataset FOREIGN KEY (id_dataset)
      REFERENCES gn_meta.t_datasets (id_dataset) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE NO ACTION
);
COMMENT ON TABLE gn_commons.cor_module_dataset IS 'Define wich datasets can be used in modules';

ALTER TABLE ref_nomenclatures.t_nomenclatures
  ADD CONSTRAINT unique_id_type_cd_nomenclature UNIQUE (id_type, cd_nomenclature);


INSERT INTO ref_nomenclatures.t_nomenclatures(
            id_type,
            cd_nomenclature,
            mnemonique,
            label_fr, 
            definition_default,
            label_fr,
            definition_fr
            )
    SELECT id_type, cd_nomenclature, mnemonique, label_default, definition_default, label_default AS label_fr, definition_default AS definition_fr  
	FROM (
		SELECT id_type,
		'POINT_ECOUTE_CHEVECHE' AS cd_nomenclature,
		'Pt. Ec. Chev.' AS mnemonique,
		'Point écoute chevêche' AS label_default,
		'Point écoute chevêche associées à un circuit pour le suivi des chouettes chevêches' AS definition_default
			FROM ref_nomenclatures.bib_nomenclature_type
			WHERE mnemonique = 'TYPE_SITE'
	)a;