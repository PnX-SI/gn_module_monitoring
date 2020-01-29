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
  * Renseigner et/ou modifier les valeurs du fichier ``contrib/test/custom.json`` (voir `Configuration du module de suivi générique`_ pour les détails).


========================
Exemples de sous-modules
========================

D'autres exemples de sous-modules sont disponibles sur le dépôt https://github.com/PnCevennes/protocoles_suivi :

* protocole de suivi des oedicnèmes,
* protocole de suivi des mâles chanteurs de l'espèce chevêche d'Athena.

=========================
Création d'un sous-module
=========================

---------------------
Structure d'un module
---------------------

* ``config.json`` `(config. générale)`
* ``custom.json`` `(config. spécifique à la base)`
* ``module.json`` `(config. du module)`
* ``site.json`` `(config. des sites)`
* ``visit.json`` `(config. des visites)`
* ``observation.json`` `(config. des observations)`
* ``nomenclature.json`` `(pour l'ajout de nomenclatures spécifiques au sous-module)`

Pour chaque fichier, les valeurs prisent par défaut sont celle du fichier de même nom présent dans le répertoire ``config/monitoring/generic``.

------------------------------------
Le dossier config/monitoring/generic
------------------------------------



