---
subtitle: 'Création d''un sous-module'
title: 'Création d''un sous-module'
---

- [Structure d'un module](#structure-dun-module)
  - [La configuration](#la-configuration)
  - [Les exports](#les-exports)
- [Configuration générale](#configuration-générale)
- [Configuration des objets](#configuration-des-objets)
  - [Les schémas génériques](#les-schémas-génériques)
      - [Liste des widgets disponibles](#liste-des-widgets-disponibles)
      - [Listes des paramètres disponibles par type de widgets :](#listes-des-paramètres-disponibles-par-type-de-widgets-)
  - [Définir une nouvelle variable](#définir-une-nouvelle-variable)
  - [Redéfinir une variable existante](#redéfinir-une-variable-existante)
  - [`datalists`](#datalists)
    - [Les paramètres dynamiques](#les-paramètres-dynamiques)
    - [La variable `change`](#la-variable-change)
- [Nomenclature](#nomenclature)
- [Configuration de la carte](#configuration-de-la-carte)
- [Exports](#exports)
  - [PDF](#pdf)
  - [CSV](#csv)

# Structure d'un module

## La configuration

* `config.json` (configuration-générale)
* `module.json` (configuration du module)
* `site.json` (configuration des sites)
* `group_site.json` (configuration des groupes de sites)
* `visit.json` (configuration des visites)
* `observation.json` (configuration des observations)
* `observation_detail.json` (configuration des détails des observations)
* `nomenclature.json` (pour l'ajout de nomenclatures spécifiques au sous-module)
* `synthese.sql` (vue pour la synchronisation avec la synthèse) voir

## Les exports

* `exports`
    * `csv`
        * *fichiers sql* qui permettent de définir les vues qui
            serviront aux exports `csv`
        * le nommage des vues doit être
            `"v_export_<module_code>_<method>`
            * `<method>` est une chaine de caractère qui permet de
                caractériser différentes vues et différents exports pour
                un module
    * `pdf`
        * *fichiers html/img/css*
            * ces fichiers definissent un template pour l'export pdf
                et tous les assets nécessaires (images, style, etc..)

Pour chaque fichier, les valeurs prises par défaut sont celles du
fichier de même nom présent dans le répertoire
`config/monitoring/generic`.

Le fichier `img.jpg` servira de vignette du sous-module sur la page
d'accueil du module Monitoring. Le format paysage est à privilégier.
Pour chacune un lien symbolique est créé automatiquement dans le
répertoire `media/monitorings/<module_code>.jpg` de GeoNature.

# Configuration générale

Dans le fichier `config.json` :

* `tree` définit les relations entre les objets

```json
    {
        "tree": {
            "module": {
                "site": {
                    "visit": {
                        "observation": {
                            "observation_detail": null
                        },
                    },
                }
            }
        }
    }
```

# Configuration des objets

Dans le fichier `module.json`, deux variables doivent obligatoirement
être définies dans ce fichier :

* `module_code`: un nom cours, en minuscule et simple, par exemple
    `cheveches` ou `oedic` pour les protocoles chevêches ou oedicnèmes.
* `module_desc`: une description succinte du module.

Dans le cas général (`module.json`, `site.json`, `visit.json`,
`observation.json`) on peut redéfinir au besoin certaines variables.

* `label` : permet de nommer les objets, par exemple `"Site"` pour
    site,
* `description_field_name` : le nom du champ qui servira à décrire le
    site (pour le titre du site), par exemple :
    * `"visit_date_min"` pour une visite,
    * `"base_site_name"` pour un site;
* `geometry_type`: pour les sites seulement, peut prendre la valeur
    `Point`, `LineString` ou `Polygon`.
* `b_draw_sites_group` : pour spécifier si l'on veut afficher un
    contour autour des sites d'un groupe de site. Ce paramètre est
    également configurable dans l'interface de configuration du module.

Les variables `display_properties` et `display_list` sont à définir pour
indiquer quelles variables seront affichées (pour la page d'un objet ou
pour les listes et dans quel ordre).

Si `display_list` n'est pas défini, il prend la valeur de
`display_properties`.

Par exemple :
```json
    "display_properties": [
      "visit_date_min",
      "observers",
      "meteo",
      "comments",
      "nb_observations"
    ]
```

## Les schémas génériques

Les schémas des variables génériques sont définis dans le repertoire
`config/monitoring/generic` dans les fichiers correspondant aux objets
et dans la variable `generic`.

Pour la suite nous prendrons exemple sur la configuration des sites, qui
sera similaire aux autres objets dans les grandes lignes.

Par exemple dans le fichier `site.json` de ce repertoire on trouve la
variable "generic" :

    "id_base_site": {
        "type_widget": "text",
        "attribut_label": "Id site",
        "hidden": true
    },
    "id_module": {
        "type_widget": "text",
        "attribut_label": "ID Module",
        "hidden": true
    },

Chaque entrée de la variable `generic` est le nom d'une variable
(`"id_base_site"`, `"id_nomenclature_type_site"`, etc...)

* les attributs obligatoires :
    * `type_widget` : renseigne à la fois sur la nature de la variable
        et sur son type d'input, pour plus de détails sur les
        différentes possibilités, voir le paragraphe [Définir une
        nouvelle variable](#définir-une-nouvelle-variable).
    * `attribut_label` : associe un nom à la variable, comme
        `"Type de site"` pour `id_nomenclature_type_site`,
* les attributs facultatifs :
    * `hidden` : permet de cacher la variable ou l'input du
        formulaire
    * `value` : permet d'attribuer une valeur par défaut
    * `required` : permet de rendre un input obligatoire
    * `definition` : permet d'ajouter une définiton à la variable
        pour aider l'utilisateur
* les attributs spéciaux :
    * `type_util`: peut prendre pour valeur `"user"`,
        `"nomenclature"`, `"dataset"` ou `"taxonomy"`. Permet
        d'indiquer qu'il s'agit ici d'un identifiant (exemple : nomenclature) et
        de traiter cette variable en fonction.

On peut mettre en valeur de ces attributs des données de la
configuration du module.

Pour cela il faut utiliser les variables suivantes :

* `__MONITORINGS_PATH`
* `__MODULE.ID_LIST_TAXONOMY`
* `__MODULE.MODULE_CODE`
* `__MODULE.ID_MODULE`
* `__MODULE.ID_LIST_OBSERVER`
* `__MODULE.TAXONOMY_DISPLAY_FIELD_NAME`

qui peuvent servir dans la définition des formulaires (en particulier
pour les datalist). Voir ci dessous

#### Liste des widgets disponibles

| Widgets      | Commentaire                                                              |
|--------------|--------------------------------------------------------------------------|
| text         | Texte sur une seule ligne                                                |
| textarea     | Texte sur une plusieurs lignes                                           |
| radio        | Choix multiples uniques                                                  |
| select       | Liste de choix unique                                                    |
| time         | Heure                                                                    |
| number       | -                                                                        |
| multiselect  | Listes de choix multiples                                                |
| html         | Insertion d'un bloc html                                                 |
| nomenclature | Liste avec vocabulaire controlé de GeoNature                             |
| taxonomy     | Selection d'un taxon                                                     |
| observers    | Selection d'un observateur                                               |
| date         | Sélection d'une date                                                     |
| datalist     | Liste dont les items sont fournies par une API (externe ou interne à GN) |
|              |                                                                          |


#### Listes des paramètres disponibles par type de widgets :

| Widgets                                 | Paramètres             | Commentaire                                                                                                                                       |
|-----------------------------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| Tous                                    | attribut_label         | Label du formulaire                                                                                                                               |
| Tous                                    | definition             | Ajoute une tooltip avec le contenu de ce paramètre (le paramètre `link_definition` ne doit pas être défini)                                        |
| Tous                                    | required               | Booléen : permet de rendre obligatoire cet input                                                                                                  |
| Tous                                    | hidden                 | Booléen : permet de cacher un formulaire                                                                                                          |
| Tous                                    | link_definition        | Ajoute un lien vers l'addresse pointé par ce paramètre. Le paramètre `definition` doit également être définit                                     |
| Tous                                    | pattern_message        | Ajoute un texte en rouge sous le formulaire explicitant une erreur sur le champ                                                                   |
| Tous                                    | value                  | Valeur par défaut du formulaire                                                                                                                   |
| select / multiselect / checkbox / radio | values                 | Valeurs de choix proposées. Attend une tableau de valeur ou un tableau clé/valeur `[{"value": "my_database_value", "label": "my_display_value"}]` |
| select                                  | noNullOption           | Désactive la valeur vide ("-") des choix d'un select                                                                                              |
| number                                  | min                    | Valeur minimum de l'input                                                                                                                         |
| number                                  | max                    | Valeur maximum de l'input                                                                                                                         |
| nomenclature                            | code_nomenclature_type | Code de la nomenclature à afficher                                                                                                                |
| nomenclature                            | cd_nomenclatures       | Liste des codes nomenclatures à afficher (afin d'éliminer certains items de nomenclatures que l'on ne veut pas pour ce sous-module)               |
| nomenclature / dataset                  | multi_select           | Booléan : permet de seléctionner plusieurs items de nomenclatures                                                                                 |
| dataset                                 | module_code            | Limite aux jeu de données associés à ce module                                                                                                    |
| html                                    | html                   | Contenu du bloc html                                                                                                |

## Définir une nouvelle variable

Pour définir une nouvelle variable ou aussi redéfinir une
caractéristique d'une variable générique, il faut créer une variable
nommée `specific` dans les fichiers `site.json`, `visit.json` ou
`observation.json` afin de définir le schéma spécifique pour cet objet.

* **texte** : une variable facultative
```json
"nom_contact": {
    "type_widget": "text",
    "attribut_label": "Nom du contact"
}
```

* **entier** : exemple avec un numéro du passage compris entre 1 et 2
    est obligatoire
```json
"num_passage": {
    "type_widget": "number",
    "attribut_label": "Numéro de passage",
    "required": true,
    "min": 1,
    "max": 2
}
```

* **utilisateur** : choix de plusieurs noms d'utilisateurs dans une
    liste
```json
"observers": {
    "attribut_label": "Observateurs",
    "type_widget": "observers",
    "type_util": "user",
    "code_list": "__MODULE.ID_LIST_OBSERVER",
},
```

Il est important d'ajouter `"type_util": "user"`.

* **nomenclature** : un choix obligatoire parmi une liste définie par
    un type de nomenclature
```json
"id_nomenclature_nature_observation": {
    "type_widget": "nomenclature",
    "attribut_label": "Nature de l'observation",
    "code_nomenclature_type": "OED_NAT_OBS",
    "required": true,
    "type_util": "nomenclature"
},
```

La variable `"code_nomenclature_type": "OED_NAT_OBS",` définit le
type de nomenclature.

Il est important d'ajouter `"type_util": "nomenclature",`.

* **liste** : une liste déroulante simple, non basée sur une
    nomenclature

```json
"rain": {
    "type_widget": "select",
    "required": true,
    "attribut_label": "Pluie",
    "values": ["Absente", "Intermittente", "Continue"]
},
```

    Il est possible de définir une valeur par défaut pré-selectionnée
    avec le paramètre `value` (exemple : `"value": "Absente"`).

* **radio** : bouton radio pour un choix unique parmi plusieurs
    possibilités

```json
"beginner": {
    "type_widget": "radio",
    "attribut_label": "Débutant",
    "values": ["Oui", "Non"]
},
```
* **taxonomie** : une liste de taxons

```json
"cd_nom": {
    "type_widget": "taxonomy",
    "attribut_label": "Taxon",
    "type_util": "taxonomy",
    "required": true,
    "id_list": "__MODULE.ID_LIST_TAXONOMY"
},
```

La variable `"id_list": "__MODULE.ID_LIST_TAXONOMY"` définit la
liste de taxons.

Il est important d'ajouter `"type_util": "taxonomy",`.

* **dataset** : une liste de jeux de données

```json
        "id_dataset": {
            "type_widget": "dataset",
            "attribut_label": "Jeu de données",
            "type_util": "dataset",
            "required": true,
            "module_code": "__MODULE.MODULE_CODE",
        },

```

La variable `"module_code": "__MODULE.MODULE_CODE"` permet de
selectionner uniquement les jeux de données associés au module.

Il est important d'ajouter `"type_util": "dataset",`.


## Redéfinir une variable existante

Dans plusieurs cas, on peut avoir besoin de redéfinir un élément du
schéma.

On rajoutera cet élément dans notre variable `specific` et cet élément
sera mis à jour :

* Changer le label d'un élément et le rendre visible et obligatoire

        "visit_date_max": {
            "attribut_label": "Date de fin de visite",
            "hidden": false,
            "required": true
        }

* Donner une valeur par défaut à une nomenclature et cacher l'élément

    Dans le cas où la variable `type_widget` est redéfinie, il faut
    redéfinir toutes les variables.

```json
    "id_nomenclature_type_site": {
        "type_widget": "text",
        "attribut_label": "Type site",
        "type_util": "nomenclature",
        "value": {
            "code_nomenclature_type": "TYPE_SITE",
            "cd_nomenclature": "OEDIC"
        },
        "hidden": true
    }
```

Il est important d'ajouter `"type_util": "nomenclature",`.

Pour renseigner la valeur de la nomenclature, on spécifie :
 * le type de nomenclature `"code_nomenclature_type"` (correspond au champs mnemonique du type)
 * le code de la nomenclature `"cd_nomenclature"`

## `datalists`

Pour pouvoir faire des composants de type select à partir d'une API, on
peut utiliser le composant `datalist`.

Les options supplémentaires pour ce widget :

* `api` : API qui fournira la liste
* `application` : `GeoNature` ou `TaxHub` permet de préfixer l'API
    avec l'URL de l'API de l'application
* `keyValue` : champs renvoyé
* `keyLabel` : champs affiché
* `type_util` : `nomenclature`, `dataset`, `user` : pour le traitement
    des données par ailleurs
* `data_path` : si l'API renvoie les données de la forme
    `data: [<les données>]` alors `data_path = "data"`
* `filters` : permet de filtrer les données reçues
    (`{field_name: [value1, value2, ...]}`)
* `default` : permet de donner une valeur par defaut
    (`"default": {"cd_nomenclature": "1"}` permettra de récupérer le
    premier objet de la liste qui correspond)

Par exemple :

* Nomenclature avec sous-liste et valeur par defaut

```json
"id_nomenclature_determination_method": {
    "type_widget": "datalist",
    "attribut_label": "Méthode de détermination",
    "api": "nomenclatures/nomenclature/METH_DETERMIN",
    "application": "GeoNature",
    "keyValue": "id_nomenclature",
    "keyLabel": "label_fr",
    "data_path": "values",
    "type_util": "nomenclature",
    "required": true,
    "default": {
        "cd_nomenclature": "1"
    }
},
```

* Groupe de sites

```json
    "id_sites_group": {
        "type_widget": "datalist",
        "attribut_label": "Groupe de sites",
        "hidden": true,
        "type_util": "sites_group",
        "keyValue": "id_sites_group",
        "keyLabel": "sites_group_name",
        "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/sites_group?id_module=__MODULE.ID_MODULE&fields=id_sites_group&fields=sites_group_name",
        "application": "GeoNature"
    },
```

* Utilisateur

```json
"observers": {
    "type_widget": "datalist",
    "attribut_label": "Observateurs",
    "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
    "application": "GeoNature",
    "keyValue": "id_role",
    "keyLabel": "nom_complet",
    "type_util": "user",
    "multiple": true,
    "required": true
},
```

### Les paramètres dynamiques

Il est possible de définir des paramètre qui peuvent dépendre de
plusieurs variables. La valeur de ce paramètre est alors une chaîne de
caractère qui définit une fonction, qui utilise les variables suivantes

**Ce cas n'est pris en compte que pour les composants spécifiques, ou
pour les composants redéfinis dans `specific`**

* `value` : les valeurs du formulaire
* `attribut_name` : du composant concerné
* `meta` : un dictionnaire de données additionelles, et fourni au
    composant dynamicFormGenerator, il peut contenir des données sur
    * la nomenclature (pour avoir les valeurs des nomenclature à
        partir des id, ici un dictionnaire avec `id_nomenclature` comme
        clés.
    * `bChainInput` si on enchaine les relevés
    * etc.. à redéfinir selon les besoins

La chaine de caractère qui décrit la fonction doit être de la forme
suivante :

```json
    "hidden": "({value, attribut_name, }) => { return value.id == 't' }"
```

Le format JSON ne permet pas les sauts de ligne dans les chaines de
caractère, et pour avoir plus de lisibilité, quand la fonction est plus
complexe, on peut aussi utiliser un tableau de chaine de caractères :

```json
    "hidden": [
        "({value, attribut_name, }) => {",
        "return value.id == 't'",
        "}"
    ]
```

Le lignes seront collées entre elles avec l'ajout de saut de lignes
(caractère [n]{.title-ref}).

Il faut être certain de sa fonction.

Exemples :

* Afficher le composant `test2` et le rendre obligatoire seulement si
    `test1` a pour valeur `t` :

```json
"specific": {
    "test": {
        "type_widget": "text",
        "attribut_label": "Test"
        },
        "test2": {
        "type_widget": "text",
        "attribut_label": "Test 2",
        "hidden": "({value}) => value.test != 't'",
        "required": "({value}) => value.test != 't'"
        }
}
```

* Ajouter un champs pour renseigner la profondeur d'une grotte si le
    type de site est une grotte

Dans le fichier `site.json`

```json
"specific": {
    ...
    "profondeur_grotte": {
    "type_widget": "number",
    "attribut_label": "Profondeur de la grotte",
    "hidden": "({value, meta}) => meta.nomenclatures[value.id_nomenclature_type_site] || {}).cd_nomenclature !== '1'",
    "required": "({value, meta}) => (meta.nomenclatures[value.id_nomenclature_type_site] || {}).cd_nomenclature === '1'"
    }
    ...
}
```

**Le paramêtre ``value`` ne peut pas être dynamique, pour changer la
valeur des variables en fonction d'autres variables, on peut définir
``change`` dans la config. Voir ci dessous**

### La variable `change`

On peut y définir une fonction qui sera appelée chaque fois que le
formulaire change.

Un exemple (`module.json` du module test) :

```json
{
    "module_label":"Test",
    "module_desc":"Module de test pour le module de suivi générique",
    "specific": {
        "test": {
            "type_widget": "text",
            "attribut_label": "Test"
        },
        "test2": {
            "type_widget": "text",
            "attribut_label": "Test 2 (hidden)",
            "hidden": "({value}) => value.test != 't'"
        },
        "test3": {
            "type_widget": "text",
            "attribut_label": "Test 3 (change)"
        }
    },
    "change": [
        "({objForm, meta}) => {",
            "const test3 = '' + (objForm.value.test || '') + '_' + (objForm.value.test2 || '');",
            "if (!objForm.controls.test3.dirty) {",
                "objForm.patchValue({test3})",
            "}",
        "}",
        ""
    ]
}
```

Ici on donne à la variable `test3` la valeur `<test>_<test2>`.

C'est valable tant que le `test3` n'a pas été modifé à la main (i. e.
`objForm.controls.test3.dirty` n'est pas vrai).

On peut donc modifer par la suite la valeur de test3 à la main.

Comme précemment on peut aussi avoir accès à meta.

# Nomenclature

Le fichier `nomenclature.json` permet de renseigner les nomenclatures
spécifiques à chaque sous-module.

Elles seront insérées dans la base de données lors de l'installation du
sous-module (si elles n'existent pas déjà).

Exemple de fichier :

```json
{
"types": [
    {
    "mnemonique": "TEST_METEO",
    "label_default": "Météo",
    "definition_default": "Météo (protocôle de suivi test)"
    }
],
"nomenclatures": [
    {
    "type":"TEST_METEO",
    "cd_nomenclature": "METEO_B",
    "mnemonique": "Beau",
    "label_default": "Beau temps",
    "definition_default": "Beau temps (test)"
    },
    {
    "type":"TEST_METEO",
    "cd_nomenclature": "METEO_M",
    "mnemonique": "Mauvais",
    "label_default": "Mauvais temps",
    "definition_default": "Mauvais temps (test)"
    }
]
}

```

**Attention** : si une nomenclature de même `type` et `cd_nomenclature`
existe déjà elle ne sera pas modifiée.


# Configuration de la carte

Il est possible d'afficher des popups sur la carte et de choisir la
valeur à afficher.

Pour cela éditez le fichier de configuration associé (`module.json`,
`site.json`, `visite.json`) et rajoutez la variable suivante :

    "map_label_field_name": <nom_du_champs>,

NB : pour ajouter une popup sur la liste des sites, éditez le fichier
`module.json`, pour la liste des visites le fichier `site.json` etc....


# Exports

Il est possible de configurer des exports (CSV ou PDF).

## PDF

Les fichiers de template (`.html`) et assets (images, style, etc..) pour
l'export PDF sont à placer dans le dossier `<module_code>/exports/pdf/`

* Dans le fichier de config d'un objet (par exemple
    `sites_group.json`:

    * ajouter la variable `export_pdf`:
```json
"export_pdf": [
    {
        "template": "fiche_aire.html",
        "label": "Export PDF"
    }
]
```

* Dans les fichiers template on a accès à la variable `data`, un
    dictionnaire contenant :
    * `static_pdf_dir` : chemin du dossier des assets de l'export pdf
    * `map_image` : l'image tirée de la carte leaflet
    * `monitoring_object.properties` : propriété de l'objet courant
* La commande `geonature monitorings process_export_pdf <module_code>`
    permet de :
    * placer les fichier de template en `.html` (lien symbolique) dans
        le dossier
        `<geonature>/backend/template/modules/monitorings/<module_code>`
    * placer les fchiers d'assets dans le dossier static :
        `<geonature>/backend/media/monitorings/<module_code>/exports/pdf`

## CSV

Les fichiers `.sql` qui définissent les vues pour l'export CSV sont
placés dans le dossier `<module_code>/exports/csv/`.

* Dans le fichier de config du module (`module.json`) ou d'un objet
    (par exemple `sites_group.json`) :

    * ajouter la variable `export_csv`:
```json
"export_csv": [
    { "label": "Format standard CSV", "type":"csv" , "method": "standard" , "filter_dataset": true},
    { "label": "Format analyses CSV", "type":"csv" , "method": "analyses" }
],
```

* Paramètres :
    * `label` : Nom de l'export
    * `method` : Nom de la vue sans le code du module
    * `filter_dataset` (true|false) : Ajoute le filtre des datasets.
        Dans ce cas il faut que la vue ait un champ `id_dataset`
* La commande `geonature monitorings process_export_csv <module_code>`
    permet de :
    * exécuter tous les fichiers SQL de ce répertoire
    * les vues doivent être nommées `v_export_<module_code>_<method>`
