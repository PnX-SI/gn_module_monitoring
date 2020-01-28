
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
geonature install_gn_module <mon_chemin_absolu_vers_le_module> monitoring
```
 * Vous pouvez sortir du venv en lançant la commande `deactivate`

## Configuration du module


    * Placer vous à la racine du dossier du module

    * Copier le fichier `config/monitoring/generic/config_custom.json.sample` dans `config/monitoring/generic/config_custom.json`
    `cp config/monitoring/generic/config_custom.json.sample`
    
    * Ce fichier reseigne les valuer qui vont servir pour les composants des formulaires. 
```
{
  "__CODE_LIST_INVENTOR": "obsocctax",
  "__CODE_LIST_OBSERVER": "obsocctax",
  "__ID_COMPONENT_TAXONOMY": "100",
  "__ID_DATASET_VISIT": 1
}   
```
Les Valeurs renseignées dans ce fichier peuvent servir pour tous les sous-modules, ou bien peuvent être redéfinie dans le fichier du même nom `config_custom.json` propre au sous-module.

** `__CODE_LIST_OBSERVER` : renseigne le code de la liste utilisateur pour les observateurs du protocole.
  Il est par defaut mis à `obsocctax` mais une liste spécifique peut être précisée.
** `__CODE_LIST_INVENTER` : renseigne la liste des descripteurs de sites.
** `__ID_COMPONENT_TAXONOMY` : renseigne l'id de la liste de taxon qui concernent un module. Il est en général propre à chaque sous module et devrai être redéfini pour chaque sous-module.
** `__ID_DATASET_VISIT` : renseigne le jeu de donnée correspondant à aux visites. Il est en général propre à chaque sous module et devrai être redéfini pour chaque sous-module.

## Installaton du module de test



* S'assurer d'être dans le virtualenv


* Executer la commande

```
    flask monitoring install <mon_chemin_absolu_vers_le_module>/contrib/test test
```

## Customisation 

## Création d'un nouveau module
TODO
