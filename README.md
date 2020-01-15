
# GeoNature Monitoring


Module générique de gestion des données de protocoles de type suivis

Ce module permet de gérer de façon générique des données de protocoles "simples". Les données spécifiques à chaque protocole sont stockées en base de données sous forme de jsonb.


## Installation du module


   * Installez GeoNature (https://github.com/PnX-SI/GeoNature)
   * Téléchargez la dernière version stable du module (wget https://github.com/PnX-SI/gn_module_monitoring/archive/X.Y.Z.zip ou en cliquant sur le bouton GitHub "Clone or download" de cette page) dans /home/myuser/
   * Dézippez la dans /home/myuser/ (unzip X.Y.Z.zip)
   * Renommer le répertoire mv gn_module_monitoring-X.Y.Z gn_module_monitoring
   * Installez les librairies frontend necessaire au module
```
cd /home/`whoami`/gn_module_monitoring/frontend
npm install
```

   * Placez-vous dans le répertoire backend de GeoNature et lancez les commandes suivantes :
```
source venv/bin/activate 
geonature install_gn_module <mon_chemin_absolu_vers_le_module> /monitoring
```

    * Vous pouvez sortir du venv en lançant la commande `deactivate`


## Ajout du module de test

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

## Customisation 
Modifier les valeurs du fichier `config/monitoring/generic/config_custom.json`

## Création d'un nouveau module
