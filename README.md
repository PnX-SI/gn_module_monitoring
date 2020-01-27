
# GeoNature Monitoring


Module générique de gestion des données de protocoles de type suivis

Ce module permet de gérer de façon générique des données de protocoles "simples". Les données spécifiques à chaque protocole sont stockées en base de données sous forme de jsonb.

## Module de test

Liste des protocoles de suivis
![Liste des protocoles de suivis](/docs/images/suivis_list_modules.png)
Liste des sites du protocole de test
![Liste des sites du protocole de test](/docs/images/suivis_list_sites.png)
Détail d'un site du protocole de test
![Détail d'un site du protocole de test](/docs/images/suivis_detail_site.png)
Formulaire des sites du protocole de test
![Formulaire des sites du protocole de test](/docs/images/suivis_form_site.png)
Formulaire des visites du protocole de test
![Formulaire des visites du protocole de test](/docs/images/suivis_form_visite.png)
Détail d'une visite du protocole de test
![Détail d'une visite du protocole de test](/docs/images/suivis_detail_observation.png)

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


## Installaton du module de test



* S'assurer d'être dans le virtualenv


* Executer la commande

```
    flask monitoring install <mon_chemin_absolu_vers_le_module>/contrib/test test
```

## Customisation 
Modifier les valeurs du fichier `config/monitoring/generic/config_custom.json`

## Création d'un nouveau module
TODO
