# Ajout d'un nouveau module

```
--Création d'un module

INSERT INTO gn_commons.t_modules(
    module_label, module_desc, 
    module_path, module_target,
    active_frontend, active_backend, module_code
)
VALUES (
    'test',  'Module de suivis des test', 
    'test', '_self', 
    false, false, 'GN_MONITORING_TEST'
);
 
--  Récupération de l'id module et insertion dans la table complément
INSERT INTO gn_monitoring.t_module_complements (id_module)
SELECT id_module
FROM  gn_commons.t_modules 
WHERE module_code = 'GN_MONITORING_TEST';


```

# Customisation 
Modifier les valeurs du fichier `config/monitoring/generic/config_custom.json`