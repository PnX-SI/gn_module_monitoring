
# GeoNature Monitoring


Module générique de gestion des données de protocoles de type suivis

Ce module permet de gérer de façon générique des données de protocoles "simples". Les données spécifiques à chaque protocole sont stockées en base de données sous forme de jsonb.

## Apperçu

Liste des sites du protocole de test
![Liste des sites du protocole de test](/docs/images/suivis_list_sites.png)

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

### Configuration du module

  * Placer vous à la racine du dossier du module

  * Copier le fichier `config/monitoring/generic/config_custom.json.sample` dans `config/monitoring/generic/config_custom.json`
    
    ```cp config/monitoring/generic/config_custom.json.sample```
    
  * Ce fichier reseigne les valuer qui vont servir pour les composants des formulaires. 
```
{
  "__CODE_LIST_INVENTOR": "obsocctax",
  "__CODE_LIST_OBSERVER": "obsocctax",
  "__ID_COMPONENT_TAXONOMY": "100",
  "__ID_DATASET_VISIT": 1
}   
```
Les Valeurs renseignées dans ce fichier peuvent servir pour tous les sous-modules, ou bien peuvent être redéfinies dans le fichier du même nom `config_custom.json` propre au sous-module.

  * `__CODE_LIST_OBSERVER` : renseigne le code de la liste utilisateur pour les observateurs du protocole.
  Il est par defaut mis à `obsocctax` mais une liste spécifique peut être précisée.
  * `__CODE_LIST_INVENTER` : renseigne la liste des descripteurs de sites.
  * `__ID_COMPONENT_TAXONOMY` : renseigne l'id de la liste de taxon qui concernent un module. Il est en général propre à chaque sous module et devrai être redéfini pour chaque sous-module.
  * `__ID_DATASET_VISIT` : renseigne le jeu de donnée correspondant à aux visites. Il est en général propre à chaque sous module et devrai être redéfini pour chaque sous-module.

## Installaton du module de test

  * S'assurer d'être dans le virtualenv.

  * Executer la commande.

```
    flask monitoring install <mon_chemin_absolu_vers_le_module>/contrib/test test
```

### Configuration du module de test

  * Copier le fichier `config/monitoring/generic/config_custom.json` dans `config/monitoring/test/config_custom.json`.
  
  * Renseigner et/ou modifier les valeurs du fichier `contrib/test/config_custom.json` (voir l eparagraphe configuration du module pour les détails).

## Autres exemples

  * D'autres exemples de sous-modules sont disponible au dépôt [protocole_suivi](https://github.com/PnCevennes/protocoles_suivi) :
    * protocole de suivi des oedicnèmes,
    * protocole de suivi des mâles chanteurs de la chouette chevêche Athena.

## Création d'un nouveau module

### Structure des données génériques
  - /
    - `config_object.json` *(définition générales)*
    - `config_custom.json` *(configuration propre à chaque installation)*
    - `config_data.json` *(définition des données à pré-charger)*
    - `schema_module.json` *(définition des variables du module)*
    - `schema_site.json` *(définition des variables des sites)*
    - `schema_visit.json` *(définition des variables des visites)*
    - `schema_observation.json` *(définition des variables des observations)*

#### `config_object.json`

##### La variable `tree`
Cette  variable renseigne l'arborescence du module et defini les relation de parenté entre les objets.

```
  "tree": {
      "module": {
        "site": {
          "visit": {
            "observation": null
          }
        }
      }
    }
```
##### Configuration pour chaque `<object_type>`
```


  "site": {
    "id_field_name": "id_base_site",
    "description_field_name": "base_site_name",
    "label": "Site",
    "geom_field_name": "geom",
    "uuid_field_name": "uuid_base_site",
    "geometry_type": "Point",
    "display_properties": [
      "base_site_name",
      "base_site_code",
      "id_nomenclature_type_site",
      "id_inventor",
      "first_use_date",
      "last_visit",
      "nb_visits"
    ],
    "display_list": [
      "base_site_name",
      "base_site_code",
      "id_nomenclature_type_site",
      "last_visit",
      "nb_visits"
    ],
    "sorts": [
      {"prop": "last_visit", "dir": "desc"}
    ]
  }
```
  * `label` :
  * `id_field_name`, `uuid_field_name` :
  * `description_field_name` : 
  * `geom_field_name`, `geometry_type` :
  * `

#### `config_custom.json`

#### `config_data.json`

#### `schema_<object_type>`


### Struture d'un module


### Définir un schéma

#### Ajouter une variable

#### Redefinir un composant

#### Les différent types de composant
