Création d'un sous-module
#########################

=========================
Création d'un sous-module
=========================

* `Structure d'un module`_
* `Configuration générale`_
* `Configuration des objets`_
* `Nomenclature`_

---------------------
Structure d'un module
---------------------

* ``config.json`` `(configuration générale)`
* ``module.json`` `(configuration du module)`
* ``site.json`` `(configuration des sites)`
* ``group_site.json`` `(configuration des groupes de sites)`
* ``visit.json`` `(configuration des visites)`
* ``observation.json`` `(configuration des observations)`
* ``nomenclature.json`` `(pour l'ajout de nomenclatures spécifiques au sous-module)`
* ``synthese.sql`` `(vue pour la synchronisation avec la synthèse)` voir

Pour chaque fichier, les valeurs prises par défaut sont celles du fichier de même nom présent dans le répertoire ``config/monitoring/generic``.

Le fichier ``img.jpg`` servira de vignette du sous-module sur la page d'accueil du module Monitorings.
Pour chacune un lien symbolique est créé automatiquement dans le répertoire ``frontend/src/external_assets/monitorings`` de GeoNature. 

Pour que l'image soit prise en compte, lors de l'installation du module ou si on la modifie, il faut relancer une compilation de GeoNature (avec la commande ``geonature frontend_build`` par exemple).


----------------------
Configuration générale
----------------------

Dans le fichier ``config.json`` :

* ``tree`` définit les relations entre les objets


.. code-block:: JSON

    {
        "tree": {
            "module": {
                "site": {
                "visit": {
                    "observation": null
                },
            }
        }
    }

------------------------
Configuration des objets
------------------------

Dans le fichier ``module.json``, deux variables doivent obligatoirement être définies dans ce fichier :

* ``module_code``: un nom cours, en minuscule et simple, par exemple ``cheveches`` ou ``oedic`` pour les protocoles chevêches ou oedicnèmes.
* ``module_desc``: une description succinte du module.

Dans le cas général (``module.json``, ``site.json``, ``visit.json``, ``observation.json``) on peut redéfinir au besoin certaines variables.

* ``label`` : permet de nommer les objets, par exemple ``"Site"`` pour site,
* ``description_field_name`` : le nom du champs qui servira à décrire le site (pour le titre du site), par exemple :
    * ``"visit_date_min"`` pour une visite,
    * ``"base_site_name"`` pour un site;
* ``geometry_type``: pour les sites seulement, peut prendre la valeur ``Point``, ``LineString`` ou  ``Polygon``.

Les variables ``display_properties`` et ``display_list`` sont à définir pour indiquer quelles variables seront affichées (pour la page d'un objet ou pour les listes et dans quel ordre).

Si ``display_list`` n'est pas défini, il prend la valeur de ``display_properties``.

Par exemple :

.. code-block:: JSON

  "display_properties": [
    "visit_date_min",
    "observers",
    "meteo",
    "comments",
    "nb_observations"
  ],


  Les schémas
===========

Les schémas génériques
----------------------

Les schémas des variables génériques sont définis dans le repertoire ``config/monitoring/generic`` dans les fichiers correspondant aux objets et dans la variable ``generic``.

Pour la suite nous prendrons exemple sur la configuration des sites, qui sera similaire aux autres objets dans les grandes lignes.

Par exemple dans le fichier ``site.json`` de ce repertoire on trouve la variable "generic" :

.. code-block:: JSON

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

Chaque entrée de la variable ``generic`` est le nom d'une variable (``"id_base_site"``, ``"id_nomenclature_type_site"``, etc...)

* les attributs obligatoires :
    * ``type_widget`` : renseigne à la fois sur la nature de la variable et sur son type d'input, pour plus de détails sur les différentes possibilités, voir le  paragraphe `Définir une nouvelle variable`_.
    * ``attribut_label`` : associe un nom à la variable, comme ``"Type de site"`` pour ``id_nomenclature_type_site``,
* les attributs facultatifs :
    * ``hidden`` : permet de cacher la variable ou l'input du formulaire,
    * ``value`` : permet d'attribuer une valeur par défaut,
    * ``required`` : permet de rendre un input obligatoire.
    * ``definition`` : permet d'ajouter une définiton à la variable pour aider l'utilisateur.
* les attributs `spéciaux` :
    * ``type_util``: peut prendre pour valeur ``"user"``, ``"nomenclature"`` ou  ``"taxonomy"``. Permet d'indiquer qu'il s'agit ici d'une id (d'une nomenclature) et de traiter cette variable en fonction.

On peut mettre en valeur de ces attribut des données de la configuration du module.
Pour ce il faut utiliser les variables suivantes

* ``__MONITORINGS_PATH``
* ``__MODULE.__ID_COMPONENT_TAXONOMY``
* ``__MODULE.MODULE_CODE``
* ``__MODULE.ID_MODULE``
* ``__MODULE.ID_LIST_OBSERVER``
* ``__MODULE.TAXONOMY_DISPLAY_FIELD_NAME``

qui peuvent servir dans la définition des formulaire (en particulier pour les datalist) voir ci dessous

Définir une nouvelle variable
-----------------------------

Pour définir une nouvelle variable ou aussi redéfinir une caractéristique d'une variable générique, il faut créer une variable nommée ``specific`` dans les fichiers ``site.json``, ``visit.json`` ou ``observation.json`` afin de définir le schéma spécifique pour cet objet.

* **texte** : une variable facultative

.. code-block:: JSON

        nom_contact": {
            "type_widget": "text",
            "attribut_label": "Nom du contact"
        }

* **entier** : exemple avec un numéro du passage compris entre 1 et 2 est obligatoire

.. code-block:: JSON

        "num_passage": {
            "type_widget": "number",
            "attribut_label": "Numéro de passage",
            "required": true,
            "min": 1,
            "max": 2
        }
    
* **utilisateur** : choix de plusieurs noms utilisateurs dans une liste

.. code-block:: JSON

        "observers": {
            "attribut_label": "Observateurs",
            "type_widget": "observers",
            "type_util": "user",
            "code_list": "__MODULE.ID_LIST_OBSERVER",
        },


Il est important d'ajouter ``"type_util": "user",``.

* **nomenclature** : un choix obligatoire parmi une liste définie par un type de nomenclature

.. code-block:: JSON

        "id_nomenclature_nature_observation": {
            "type_widget": "nomenclature",
            "attribut_label": "Nature de l'observation",
            "code_nomenclature_type": "OED_NAT_OBS",
            "required": true,
            "type_util": "nomenclature"
        },

La variable ``"code_nomenclature_type": "OED_NAT_OBS",`` définit le type de nomenclature.

Il est important d'ajouter ``"type_util": "nomenclature",``.

* **liste** : une liste déroulante simple, non basée sur une nomenclature

.. code-block:: JSON

        "rain": {
            "type_widget": "select",
            "required": true,
            "attribut_label": "Pluie",
            "values": ["Absente", "Intermittente", "Continue"]
        },

Il est possible de définir une valeur par défaut pré-selectionnée avec le paramètre ``value`` (exemple : ``"value": "Absente"``).

* **radio** : bouton radio pour un choix unique parmi plusieurs possibilités

.. code-block:: JSON

        "beginner": {
            "type_widget": "radio",
            "attribut_label": "Débutant",
            "values": ["Oui", "Non"]
        },

* **taxonomie** : une liste de taxons

.. code-block:: JSON

        "cd_nom": {
            "type_widget": "taxonomy",
            "attribut_label": "Taxon",
            "type_util": "taxonomy",
            "required": true,
            "id_list": "__MODULE.__ID_COMPONENT_TAXONOMY"
        },

La variable ``"id_list": "__MODULE.__ID_COMPONENT_TAXONOMY"`` définit la liste de taxon.

Il est important d'ajouter ``"type_util": "taxonomy",``.

Redéfinir une variable existante
--------------------------------

Dans plusieurs cas, on peut avoir besoin de redéfinir un élément du schéma.

On rajoutera cet élément dans notre variable ``specific`` et cet élément sera mis à jour :

* Changer le label d'un élément et le rendre visible et obligatoire

.. code-block:: JSON
    
        "visit_date_max": {
            "attribut_label": "Date de fin de visite",
            "hidden": false,
            "required": true
        }

* Donner une valeur par défaut à une nomenclature et cacher l'élément

  Dans le cas où la variable ``type_widget`` est redéfinie, il faut redéfinir toutes les variables.

.. code-block:: JSON

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

Il est important d'ajouter ``"type_util": "nomenclature",``.

Pour renseigner la valeur de la nomenclature, on spécifie :
    * le type de nomenclature ``"code_nomenclature_type"`` (correspond au champs mnemonique du type)
    * le code de la nomenclature ``"cd_nomenclature"``


``datalists``
-------------

Pour pouvoir faire des composant de type select à partir d'un api, on peut utiliser le composant ``datalist``

les options supplémentaires pour ce widget: 

- ``api`` : api qui fournira la liste
- ``application`` : ``GeoNature`` ou ``TaxHub`` permet de prefixer l'api avec l'url de l'api de l'application
- ``keyValue`` : champs renvoyé
- ``keyLabel`` : champs affiché
- ``type_util`` :``nomenclature``, ``dataset``, ``user``: pour le traitement des données par ailleur
- ``data_path`` : si l'api renvoie les données de la forme ```data: [<les données>]``` alors ``data_path = "data"``
- ``filter`` : permet de filtrer les données recu ({field_name: [value1, value2, ...]}
- ``default`` : permet de donner une valeur par defaut ("default": {"cd_nomenclature": "1"} permettra de récupérer le premier objet de la liste qui correspond)

par exemple :

* nomenclature avec sous liste et valeur par defaut

.. code-block:: JSON

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

* groupe de site

.. code-block:: JSON

    "id_sites_group": {
        "type_widget": "datalist",
        "attribut_label": "Groupe de sites",
        "hidden": true,
        "type_util": "sites_group",
        "keyValue": "id_sites_group",
        "keyLabel": "sites_group_name",
        "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/sites_group?id_module=__MODULE.ID_MODULE",
        "application": "GeoNature"
    },


* jeux de données (pour les visites on veut la liste des JDD pour le module, d'où l'utilisation de ``"module_code": "__MODULE.MODULE_CODE"`` en paramètre ``GET`` de l'api

.. code-block:: JSON

    "id_dataset": {
        "type_widget": "datalist",
        "attribut_label": "Jeu de données",
        "type_util": "dataset",
        "api": "meta/datasets",
        "application": "GeoNature",
        "keyValue": "id_dataset",
        "keyLabel": "dataset_shortname",
        "params": {
            "active": true,
            "orderby": "dataset_name",
            "module_code": "__MODULE.MODULE_CODE"
        },
        "data_path": "data",
        "required": true
    },


* utilisateur

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


.. code-block:: JSON


------------
Nomenclature
------------

Le fichier ``nomenclature.json`` permet de renseigner les nomenclatures spécifiques à chaque sous-module.
Elles seront insérées dans la base de données lors de l'installation du sous-module (si elles n'existent pas déjà). 

Exemple de fichier :

.. code-block:: JSON

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


**Attention** : si une nomenclature de même ``type`` et ``cd_nomenclature`` existe déjà elle ne sera pas modifiée.