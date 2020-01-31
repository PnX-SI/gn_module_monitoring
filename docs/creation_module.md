
# Création d'un nouveau module

## Structure des données génériques
  - /
    - [`config.json`](../config/monitoring/generic/config.json) *(définitions générales et données à pre-charger)*
    - [`custom.json`](../config/monitoring/generic/custom.json) *(configuration propre à chaque installation)*
    - [`module.json`](../config/monitoring/generic/module.json) *(configuration du module)*
    - [`site.json`](../config/monitoring/generic/site.json) *(configuration des sites)*
    - [`visit.json`](../config/monitoring/generic/visit.json) *(configuration des visites)*
    - [`observation.json`](../config/monitoring/generic/observation.json) *(configuration des observations)*

### L`config.json`

#### `tree`
Cette variable renseigne l'arborescence du module et definit les relations de parenté entre les objets.

Dans cet exemple, et dans le cas le plus général on a ici un module qui contient des sites. Ces derniers sont associés à des visites qui sont eux-même associés à des observations.

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

#### `data`

Cette variable renseigne les données à pré-charger pour les formulaires.

```
"data": {
    "nomenclature": [
        "TYPE_SITE",
        "STATUT_OBS"
    ],
    "taxonomy": {
      "cd_noms": [423718]
    },
    "user": [
      "__CODE_LIST_INVENTOR",
      "__CODE_LIST_OBSERVER"
    ]
  }
```

Dans ce cas les données pré-chargées seront :
  * les nomenclatures de type seront `TYPE_SITE` ou `STATUT_OBS`,
  * le taxon correspondant au cd_nom : `423718`,
  * les utilisteurs des listes correspondant aux valeurs définies dans le fichier [config/generic/custom.json](../config/generic/custom.json).

### Configuration 

### Configuration pour chaque type d'objet

Nous prenons exemple ici sur la configuration des sites, c'est-à-dire le fichier [config/monitoring/generic/site.json](../config/monitoring/generic/site.json)

```
{
  "id_field_name": "id_base_site",
  "description_field_name": "base_site_name",
  "label": "Site",
  "geom_field_name": "geom",
  "uuid_field_name": "uuid_base_site",
  "geometry_type": "Point",
...
```

#### Affichage des données

```
...
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
...

```

#### Tri par défaut

```
...
  "sorts": [
    {"prop": "last_visit", "dir": "desc"}
  ],
...
```

#### Définition des formulaires

```
...
"generic": {
    "id_base_site": {
      "type_widget": "text",
      "attribut_label": "Id site",
      "hidden": true
    },
    ...
    "id_nomenclature_type_site": {
      "type_widget": "nomenclature",
      "attribut_label": "Type de site",
      "code_nomenclature_type": "TYPE_SITE",
      "type_util": "nomenclature",
      "required": true,
      "hidden": true
    },
    "id_inventor": {
      "type_widget": "observers",
      "attribut_label": "Descripteur",
      "code_list": "__CODE_LIST_INVENTOR",
      "max_length": 1,
      "type_util": "user",
      "required": true
    },
    ...
    "first_use_date": {
      "type_widget": "date",
      "attribut_label": "Date description",
      "required": true
    }
  } 
```


## Struture d'un module

## Définir un schéma

### Ajouter une variable

### Redéfinir un composant

### Les différents types de composant
