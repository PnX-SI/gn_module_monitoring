==========================
Module de suivi génériques
==========================


--------------------------------------------------------------------
Module générique de gestion des données de protocoles de type suivis
--------------------------------------------------------------------

Ce module permet de gérer de façon générique des données de protocoles "simples".
Les données spécifiques à chaque protocole sont stockées en base de données sous forme de jsonb.


.. image:: docs/images/apercu.png
    :alt: Liste des sites du protocole de test
    :width: 800

* `Installation du module de suivi générique`_
* `Configuration du module de suivi générique`_
* `Installation du sous-module de test`_
* `Exemples de sous-modules`_
* `Création d'un sous-module`_


=========================================
Installation du module de suivi générique
=========================================

* Installer GéoNature (<https://github.com/PnX-SI/GeoNature>)
* Téléchargez la dernière version stable du module (wget https://github.com/PnX-SI/gn_module_monitoring/archive/X.Y.Z.zip ou en cliquant sur le bouton GitHub "Clone or download" de cette page)
* Placez-vous dans le répertoire backend de GeoNature et lancez les commandes suivantes :

::

    source venv/bin/activate 
    geonature install_gn_module <mon_chemin_absolu_vers_le_module> monitorings


------------------------------------------
Configuration du module de suivi générique
------------------------------------------

* Placer vous à la racine du module (``<chemin_vers_geonature>/external_module/monitorings``). 
* Copier le fichier ``config/monitoring/generic/custom.json.sample`` dans ``config/monitoring/generic/custom.json``

:: 

    cp config/monitoring/generic/custom.json.sample config/monitoring/generic/custom.json

* Éditer / modifier le fichier

.. code-block:: JSON

    {
        "__CODE_LIST_INVENTOR": "obsocctax",
        "__CODE_LIST_OBSERVER": "obsocctax",
        "__ID_COMPONENT_TAXONOMY": "100",
        "__ID_DATASET_VISIT": 1
    }

Les Valeurs renseignées dans ce fichier peuvent servir pour tous les sous-modules, ou bien peuvent être redéfinies dans le fichier du même nom `config_custom.json` propre au sous-module.

* ``__CODE_LIST_OBSERVER`` : le code de la liste utilisateur pour les observateurs du protocole.
  Il est par defaut mis à ``obsocctax`` mais une liste spécifique peut être précisée.
* ``__CODE_LIST_INVENTER`` : la liste des descripteurs de sites.
* ``__ID_COMPONENT_TAXONOMY`` : l'id de la liste de taxon qui concernent un module. Il est en général propre à chaque sous module et devrai être redéfini pour chaque sous-module.
* ``__ID_DATASET_VISIT`` : l'id du jeu de donnée correspondant à aux visites. Il est en général propre à chaque sous module et devrai être redéfini pour chaque sous-module.


===================================
Installation du sous-module de test
===================================

Le sous module de test est situé dans le dossier ``<mon_chemin_absolu_vers_le_module>/contrib/test``


* S'assurer d'être dans le ``virtualenv``.
* Exécuter la commande :

::

    flask monitoring install <mon_chemin_absolu_vers_le_module>/contrib/test test


------------------------------------
Configuration du sous-module de test
------------------------------------

* Copier le fichier ``config/monitoring/generic/custom.json`` dans ``config/monitoring/test/config_custom.json``.
* Renseigner et/ou modifier les valeurs du fichier ``contrib/test/custom.json`` (voir le paragraphe `Configuration du module de suivi générique`_ pour les détails).


========================
Exemples de sous-modules
========================

D'autres exemples de sous-modules sont disponibles sur le dépôt https://github.com/PnCevennes/protocoles_suivi :

* protocole de suivi des oedicnèmes,
* protocole de suivi des mâles chanteurs de l'espèce chevêche d'Athena.

=========================
Création d'un sous-module
=========================

* `structure d'un module`_
* `Configuration générale`_
* `Configuration des objects`_
* `Nomenclature`_
* `Installation du sous-module`_

---------------------
Structure d'un module
---------------------

* ``config.json`` `(config. générale)`
* ``module.json`` `(config. du module)`
* ``site.json`` `(config. des sites)`
* ``visit.json`` `(config. des visites)`
* ``observation.json`` `(config. des observations)`
* ``nomenclature.json`` `(pour l'ajout de nomenclatures spécifiques au sous-module)`

Pour chaque fichier, les valeurs prises par défaut sont celle du fichier de même nom présent dans le répertoire ``config/monitoring/generic``.

----------------------
Configuration générale
----------------------

Dans le fichier `config.json`

* ``tree`` défini les relations entre les objets :
* ``data`` défini les donées à pré-charger :


.. code-block:: JSON

    {
    "tree": {
        "module": {
            "site": {
            "visit": {
                "observation": null
            },
            "media": null
            }
        }
    },
    "data": {
        "nomenclature": [
            "TEST_METEO"
        ],
        "user": [
        "__CODE_LIST_INVENTOR",
        "__CODE_LIST_OBSERVER"
        ],
        "taxonomy": {
            "cd_noms": [ 423718 ]
        },
    }
    }

-------------------------
Configuration des objects
-------------------------

Dans le fichier ``module.json``,  deux variables doivent obligatoirement être définies dans ce fichier:

* ``module_path``: un nom cours, en minuscule et simple, par exemple ``cheveches`` ou ``oedic`` pour les protocoles chevêches ou oedicnèmes.
* ``module_desc``: une description succinte du module.

Dans le cas général (``module.json``, ``site.json``, ``visit.json``, ``observation.json``) on peut redéfinir au besoin certaines variables.

* ``label`` : permet de nommer les objets, par exemple ``"Site"`` pour site,
* ``description_field_name`` : le nom du champs qui servira à décrire le site (pour le titre du site), par exemple :
    * ``"visit_date_min"`` pour une visite,
    * ``"base_site_name"`` pour un site;
* ``geometry_type``: pour les sites seulement, peut prendre la valeur ``Point``, ``LineString`` ou  ``Polygon``.

Les variable ``display_properties`` et ``display_list`` sont à définir pour indiquer quelles variables seront affichée (pour la page d'un object ou pour les listes et dans quel ordre.

Si ``display_list`` n'est pas défini, il prend la valeur de  ``display_properties``

Par exemple:

.. code-block:: JSON

  "display_properties": [
    "visit_date_min",
    "observers",
    "meteo",
    "comments",
    "nb_observations"
  ],



Les schemas
===========

Les schémas génériques
----------------------

Les schémas des variables génériques sont définies dans le repertoire ``config/monitoring/generic`` dans les fichiers correspondant aux objets
et dans la variable ``generic``.

Pour la suite nous prendrons exemple sur la configuration des sites, qui sera similaire aux autres objets dans les grandes lignes.

Par exemple dans le fichier ``site.json`` de ce repertoire on trouve le variable "generic":

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

* les attribut obligatoires :
    * ``type_widget`` : renseigne à la fois sur la nature de la variable et sur son type d'input, pour plus de détails sur les différentes possibilités, voir le  paragraphe `Définir une nouvelle variable`_.
    * ``attribut_label`` : associe un nom à la variable, comme ``"Type de site"`` pour ``id_nomenclature_type_site``,
* les attributs facultatifs :
    * ``hidden`` : permet de cacher la variable ou l'input du formulaire,
    * ``value`` : permet d'attribuer une valeur par défaut,
    * ``required`` : permet de rendre un input obligatoire.
* les attributs `spéciaux` :
    * ``type_util``: peut prendre pour valeur ``"user"``, ``"nomenclature"`` ou  ``"taxonomy"``.  Permet d'indiquer qu'il s'agit ici d'une id (d'une nomenclature) et de traiter cette variable en fonction.


Définir une nouvelle variable
-----------------------------

    Pour définir une nouvelle variable ou aussi rédéfinir une caractéristique d'une variable générique, il faut créer un variable nommée ``specific`` dans le fichier ``site.json`` afin de définir le schéma spécifique pour cet objet.

* **texte** : une variable facultative

.. code-block:: JSON

        nom_contact": {
            "type_widget": "text",
            "attribut_label": "Nom du contact"
        }

* **entier** : le numéro du passage compris entre 1 et 2 et obligatoire

.. code-block:: JSON

        "num_passage": {
            "type_widget": "int",
            "attribut_label": "Numéro de passage",
            "required": true,
            "min": 1,
            "max": 2
        }
    
* **utilisateur** : choix de plusieurs noms utilisateurs dans une liste: 

.. code-block:: JSON

        "observers": {
            "attribut_label": "Observateurs",
            "type_widget": "observers",
            "type_util": "user",
            "code_list": "__CODE_LIST_OBSERVER",
        },

Ici la variable ``"__CODE_LIST_OBSERVER"`` sera à redéfinir dans le fichier ``custom.json`` à l'installation du sous-module.

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

* **taxonomie** : un choix dans une liste de taxon:

.. code-block:: JSON

        "cd_nom": {
            "type_widget": "taxonomy",
            "attribut_label": "Taxon",
            "type_util": "taxonomy",
            "required": true,
            "idComponent": "__ID_COMPONENT_TAXONOMY"
        },

La variable ``"idComponent": "__ID_COMPONENT_TAXONOMY"`` définit la liste de taxon.

Il est important d'ajouter ``"type_util": "taxonomy",``.

Redéfinir une variable existante
--------------------------------

Dans plusieurs cas, on peut avoir besoin de redéfinir un élément du schéma.
On rajoutera cet élément dans notre variable ``specific`` et cet élément sera mis à jour:

* Changer le label d'un élément et le rendre visible et obligatoire

.. code-block:: JSON
    
        "visit_date_max": {
            "attribut_label": "Date de fin de visite",
            "hidden": false,
            "required": true
        }

* Donner une valeur par défault à une nomenclature et cacher l'élément

    Dans le cas où la variable ``type_widget`` est redefinie, il faut redéfinir toutes les variables.

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

Il est important d'ajouter ``"type_util": "nomenclaure",``.

Pour renseigner la valeur de la nomenclature, on spécifie 
    * le type de nomenclare ``"code_nomenclature_type"`` (correspond au champs mnemonique du type)
    * le code de la nomenclature ``"cd_nomenclature"``.

------------
Nomenclature
------------

Ce fichier permet de renseigner la nomenclature spécifique au sous-module.
Elle sera insérée en base lors de l'installation du module. 

Un exemple de fichier:

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


---------------------------
Installation du sous-module
---------------------------

Procéder comme pour `Installation du sous-module de test`_
