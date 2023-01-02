=========
CHANGELOG
=========

0.4.1 (unreleased)
------------------

**Corrections**

* Correction du modèle Observation détail qui permet d'ajouter des informations sous le niveau observation

0.4.0 (2022-12-21)
------------------

Nécessite la version 2.11.0 (ou plus) de GeoNature.

**Evolutions**

* Packaging du module (#190)
* Gestion de la base de données avec Alembic (#190)
* Améliorations du typage frontend

**Corrections**

* Correction du marqueur Leaflet non visible lors de la création d'un point sur la carte (#187)
* Peuplement du champs ``gn_monitoring.t_module_complements.type`` avec la valeur ``monitoring_module`` pour les sous-modules de Monitoring (#193)
* Correction de l'utilisation des modèles de TaxRef
* Suppression de l'usage de ``MODULE_URL`` dans la configuration du module (https://github.com/PnX-SI/GeoNature/issues/2165)

**⚠️ Notes de version**

Si vous mettez à jour le module, il vous faut passer à Alembic.
Pour cela, une fois la version 2.11 (ou plus) de GeoNature installée :

* Entrer dans le virtualenv :

.. code-block:: bash

  source ~/geonature/backend/venv/bin/activate

* Installer la nouvelle version de Monitoring avec le paramètre ``--upgrade-db=false`` :

.. code-block:: bash

  geonature install-gn-module --upgrade-db=false <path_to_monitoring> MONITORINGS

* Indiquer à Alembic que votre base de données est en version 0.3.0 :

.. code-block:: bash

  geonature db stamp 362cf9d504ec                   # monitorings 0.3.0

* Mettre à jour la base de données en version 0.4.0 :

.. code-block:: bash

  geonature db upgrade monitorings@head

0.3.0 (2022-11-02)
------------------

Nécessite la version 2.10.0 (ou plus) de GeoNature.

**Evolutions**

* Compatibilité avec Angular version 12, mis à jour dans la version 2.10.0 de GeoNature (#135)
* Ajout de la commande ``synchronize_synthese`` permettant de synchroniser les données d'un sous-module vers la Synthèse (#176)
* Tri de la liste des sous-modules par nom sur la page d'accueil du module (#182)
* Ajout des champs ``altitude_min`` et ``altitude_max`` dans les informations affichables au niveau des sites (``generic/site.json``) (#170)
* Calcul de la géometrie des groupes de sites basculé au niveau backend (avec la fonction ``ST_ConvexHull`` de PostGIS qui prend l'enveloppe convexe des sites du groupe - #149)
* Amélioration du style des informations sur les fiches des objets (#151)
* Ajout d'un paramètre ``redirect_to_parent`` au niveau de ``observation.json`` permettant de rediriger vers la fiche de la visite à la fin de la saisie en mode "Enchainer les saisies", plutôt que vers la fiche de l'observation (#152)
* Ajout de la commande ``process_all`` permettant de régénérer toute la configuration d'un sous-module quand il est déjà installé en base de données
* Possibilité de transmettre la valeur du code du module dans l'export (#168)

**🐛 Corrections**

* Correction de la hauteur aléatoire du container principal (#146)
* Correction du zoom sur un objet de la carte au clic sur l'objet dans la liste (#149)
* Correction de l'affichage des tooltips quand la géométrie est un polygone (#159)
* Correction de la transformation des chaines de caractère en date (#170)
* Suppression de l'alias ``@librairies`` (#178)

0.2.10 (2022-03-02)
-------------------

Compatible avec GeoNature version 2.9.2 maximum.

**🐛 Corrections**

* Reprise de la config pour les champs de jeux de données et les observateurs
* Prise en compte du changement de l'api pour les jdd pour le choix des jdd de l'export

0.2.9 (2022-01-13)
------------------

Compatibilité avec GeoNature version 2.9.0 et plus.

**🐛 Corrections**

* Correction de la vue ``gn_monitoring.synthese_svo.sql`` permettant d'alimenter la Synthèse de GeoNature (#64)
* Reprise du composant de la liste déroulante de sélection des jeux de données, suite au passage à ``ng-select2`` dans GeoNature 2.9.0

0.2.8 (2021-12-10)
------------------

**🐛 Corrections**

* Suppression du trigger ``tri_meta_dates_change_t_module_complements`` dans le script d'installation du module (#118 et #120)
* Modification de la fonction contour des sites :

  - Un contour pour chaque groupe de sites
  - Prise en compte uniquement des sites visibles sur la carte (non filtrés) dans le calcul

* Complément des notes de version de la 0.2.7 (#119 par @maximetoma)
* Les modules POPAmphibien et POPReptile ont été déplacés dans le dépot https://github.com/PnCevennes/protocoles_suivi

0.2.7 (2021-10-26)
------------------

**⚠️ Notes de version**

Si vous mettez à jour le module :

* Nouvelles commandes pour gérer et mettre à jour les exports ``pdf`` et ``csv`` pour un module si ``module_code`` est précisé ou pour tous les modules :

**🚀 Nouveautés POPAmphibien - POPReptile**

* A partir de la version de GeoNature 2.7.5, les commandes de gestion du module ``monitorings`` sont accessibles depuis la commande ``geonature monitorings`` une fois que l'on a activé le ``venv``
* Nouvelles commandes :

  - ``geonature monitorings process_export_pdf <?module_code>``
  - ``geonature monitorings process_export_csv <?module_code>``
  - Pour gérer et mettre à jour les exports ``pdf`` et ``csv`` pour un module si ``module_code`` est précisé ou pour tous les modules

* Ajout des sous-modules POPAmphibien et POPReptile (idéalement à déplacer dans un autre dépôt)
* Possibilité de choisir la couleur du tableau pour les détails d'un objet (champs ``color`` dans le fichier ``<object_type>.json``)
* Dans la partie map, possibilité de joindre les sites par des lignes pour former automatiquement une aire et calculer sa superficie

  - (si le nombre des points est supérieur à 2)
  - configurable depuis l'édition du module (`dessin des groupe de site`)

* Possibilité de choisir l'icône du module dans le menu depuis l'édition du module
* Export PDF configurables

  - Bouton accessible depuis les détails

* Export CSV configurables

  - Bouton accessible depuis les détails
  - Modale pour choisir le JDD concerné par l'export

**🐛 Corrections**

* Rechargement de la configuration quand on modifie le module par le formulaire d'édition

**⚠️ Notes de version**

Si vous mettez à jour le module :

* Pour mettre à jour la base de données, il faut exécuter le fichier ``data/migration/migration_0.2.6_0.2.7.sql``
* Les exports nécessitent l'installation du module html2canvas. Il peut être nécessaire de mettre à jour les modules js en suivant la procédure suivante :

::

  cd path_to_geonature/frontend
  npm install external_modules/monitorings/frontend --no-save

0.2.6 (2021-07-23)
------------------

Compatible avec GeoNature à partir de sa version 2.6.2 (dont GeoNature 2.8).

**🚀 Nouveautés**

* Assets déplacés dans le dossier ``static`` (``backend/static/external_assets/monitorings/``) de GeoNature (#102)
* Dans les listes d'objets, ajout d'un bouton plus pour accéder directement à la création d'un enfant (#97)

  * par exemple depuis la liste des sites on peut accéder directement à la création d'une nouvelle visite

**🐛 Corrections**

* Chargement des commandes Flask

**⚠️ Notes de version**

* L'emplacement des images des modules (dans la page d'accueil qui permet de choisir un module) change.

Elles sont placées dans ``backend/static/external_assets/monitorings/assets``, l'avantage est qu'il n'est plus nécessaire de rebuild le frontend à l'installation d'un sous module.

* Pour les mettre à jour, veuillez exécuter la commande suivante :

::

  source /home/`whoami`/geonature/backend/venv/bin/activate
  export FLASK_APP=geonature
  flask monitorings process_img

ou bien à partir de GeoNature 2.7.3 :

::

  source /home/`whoami`/geonature/backend/venv/bin/activate
  export FLASK_APP=geonature
  geonature monitorings process_img

0.2.5 (2021-07-12)
------------------

**🐛 Corrections**

Problème de route frontend (#100)

0.2.4 (2021-06-15)
------------------

**🐛 Corrections**

* Problème de chainage des saisies
* Configuration de l'affichage des taxons lb_nom pris en compte

Version minimale de GeoNature nécessaire : 2.6.2

0.2.3 (2021-04-01)
------------------

Version minimale de GeoNature nécessaire : 2.5.5

**🐛 Corrections**

* Problème d'héritage des permissions (#78)

**⚠️ Notes de version**

Si vous mettez à jour le module :

* Suivez la procédure classique de mise à jour du module (``docs/MAJ.rst``)

0.2.2 (2021-03-22)
------------------

* Version minimale de GeoNature nécessaire : 2.5.5

**🚀 Nouveautés**

* Gestion des permissions par objet (site, groupe de site, visite, observation)
* Interaction carte liste pour les groupes de site

**🐛 Corrections**

* Affichage des tooltips pour les objets cachés #76

**⚠️ Notes de version**

Si vous mettez à jour le module :

* Pour mettre à jour la base de données, il faut exécuter le fichier ``data/migration/migration_0.2.1_0.2.2.sql``
* Suivez la procédure classique de mise à jour du module (``docs/MAJ.rst``)
* Nettoyer des résidus liées à l'ancienne versions :

::

  cd /home/`whoami`/geonature/frontend
  npm uninstall test
  npm ci /home/`whoami`/gn_module_monitoring/frontend/ --no-save

0.2.1 (2021-01-14)
------------------

* Version minimale de GeoNature nécessaire : 2.5.5

**🚀 Nouveautés**

* Amélioration des groupes de sites (#24)
* Possibilité de charger un fichier GPS ou GeoJSON pour localiser un site (#13)
* Alimentation massive de la synthèse depuis les données historiques d'un sous-module de suivi (#38)
* Pouvoir définir des champs *dynamiques*, dont les attributs peuvent dépendre des valeurs des autres composants (pour afficher un composant en fonction de la valeur d'autres composants). Voir les exemples dans le sous-module ``test``
* Pouvoir definir une fonction ``change`` dans les fichiers ``<object_type>.json`` qui est exécutée à chaque changement du formulaire.
* Champs data JSONB dans ``module_complement``
* Gestion des objets qui apparraissent plusieurs fois dans ``tree``. Un objet peut avoir plusieurs `parents`
* Améliorations grammaticales et possibilité de genrer les objets
* Choisir la possibilité d'afficher le bouton saisie multiple
* Par defaut pour les sites :

  * ``id_inventor`` = ``currentUser.id_role`` si non défini
  * ``id_digitizer`` = ``currentUser.id_role`` si non défini
  * ``first_use_date`` = ``<date courante>`` si non défini

**🐛 Corrections**

* Amélioration du titre (lisibilité et date francaise)
* Correction de la vue alimentant la synthèse
* Ajout du champs ``base_site_description`` au niveau de la configuration générique des sites (#58)

**⚠️ Notes de version**

Si vous mettez à jour le module :

* Pour mettre à jour la base de données, il faut exécuter le fichier ``data/migration/migration_0.2.0_0.2.1.sql``
* Pour mettre à jour la base de données, exécutez le fichier ``data/migration/migration_0.2.0_0.2.1.sql``
* Suivez la procédure classique de mise à jour du module (``docs/MAJ.rst``)
* Les fichiers ``config_data.json``, ``custom.json``, et/ou la variable `data` dans ``config.json`` ne sont plus nécessaires et ces données sont désormais gérées automatiquement depuis la configuration.

0.2.0 (2020-10-23)
------------------

Nécessite la version 2.5.2 de GeoNature minimum.

**Nouveautés**

* Possibilité de renseigner le JDD à chaque visite (`#30 <https://github.com/PnX-SI/gn_module_monitoring/issues/30>`__)
* Possibilité pour les administrateurs d'associer les JDD à un sous-module directement depuis l'accueil du sous-module (`#30 <https://github.com/PnX-SI/gn_module_monitoring/issues/30>`__)
* Possibilité de créer des groupes de sites (encore un peu jeune) (`#24 <https://github.com/PnX-SI/gn_module_monitoring/issues/24>`__)
* Possibilité de créer une visite directement après la création d'un site, et d'une observation directement après la création d'une visite (`#28 <https://github.com/PnX-SI/gn_module_monitoring/issues/28>`__)
* Redirection sur sa page de détail après la création d'un objet, plutôt que sur la liste (`#22 <https://github.com/PnX-SI/gn_module_monitoring/issues/22>`__)
* Mise à jour du composant de gestion et d'affichage des médias
* Ajout d'un composant de liste modulable (``datalist``) pouvant interroger une API, pouvant être utilisé pour les listes de taxons, d'observateurs, de jdd, de nomenclatures, de sites, de groupes de sites, etc... (`#44 <https://github.com/PnX-SI/gn_module_monitoring/issues/44>`__)
* Liste des observations : ajout d'un paramètre permettant d'afficher le nom latin des taxons observés (`#36 <https://github.com/PnX-SI/gn_module_monitoring/issues/36>`__)
* Simplification de la procédure pour mettre les données dans la synthèse (un fichier à copier, un bouton à cocher et possibilité de customiser la vue pour un sous-module)
* Passage de la complexité des méthodes de mise en base des données et de gestion des relation par liste d'``id`` (observateurs, jdd du module, correlations site module) vers le module `Utils_Flask_SQLA` (amélioration de la méthode ``from_dict`` en mode récursif qui accepte des listes d'``id`` et les traduit en liste de modèles), (principalement dans ``backend/monitoring/serializer.py``)
* Suppression du fichier ``custom.json`` pour gérer son contenu dans les nouveaux champs de la table ``gn_monitoring.t_module_complements`` (`#43 <https://github.com/PnX-SI/gn_module_monitoring/issues/43>`__)
* Clarification et remplacement des ``module_path`` et ``module_code`` (`#40 <https://github.com/PnX-SI/gn_module_monitoring/issues/40>`__)

**Corrections**

* Amélioration des modèles SLQA pour optimiser la partie sérialisation (`#46 <https://github.com/PnX-SI/gn_module_monitoring/issues/46>`__)
* Renseignement de la table ``gn_synthese.t_sources`` à l'installation (`#33 <https://github.com/PnX-SI/gn_module_monitoring/issues/33>`__)
* Passage du commentaire de la visite en correspondance avec le champs ``comment_context`` de la Synthèse, dans la vue ``gn_monitoring.vs_visits`` (`#31 <https://github.com/PnX-SI/gn_module_monitoring/issues/31>`__)
* Remplissage de la table ``gn_commons.bib_tables_location`` pour les tables du schéma ``gn_monitoring`` si cela n'a pas été fait par GeoNature (`#27 <https://github.com/PnX-SI/gn_module_monitoring/issues/27>`__)
* Corrections et optimisations diverses du code et de l'ergonomie
* Corrections de la documentation et docstrings (par @jbdesbas)

**⚠️ Notes de version**

Si vous mettez à jour le module depuis la version 0.1.0 :

* Les fichiers ``custom.json`` ne sont plus utiles (la configuration spécifique à une installation (liste utilisateurs, etc..)
  est désormais gérée dans la base de données, dans la table ``gn_monitoring.t_module_complements``)
* Dans les fichiers ``config.json``, la variable ``data`` (pour précharger les données (nomenclatures, etc..)) est désormais calculée depuis la configuration.
* Pour mettre à jour la base de données, il faut exécuter le fichier ``data/migration/migration_0.1.0_0.2.0.sql``
* Suivez la procédure classique de mise à jour du module (``docs/MAJ.rst``)

0.1.0 (2020-06-30)
------------------

Première version fonctionelle du module Monitoring de GeoNature. Nécessite la version 2.4.1 de GeoNature minimum.

**Fonctionnalités**

* Génération dynamique de sous-modules de gestion de protocoles de suivi
* Saisie et consultation de sites, visites et observations dans chaque sous-module
* Génération dynamique des champs spécifiques à chaque sous-module au niveau des sites, visites et observations (à partir de configurations json et basé sur le composant ``DynamicForm`` de GeoNature)
* Ajout de tables complémentaires pour étendre les tables ``t_base_sites`` et ``t_base_visits`` du schema ``gn_monitoring`` permettant de stocker dans un champs de type ``jsonb`` les contenus des champs dynamiques spécifiques à chaque sous-module
* Ajout de médias locaux ou distants (images, PDF, ...) sur les différents objets du module, stockés dans la table verticale ``gn_commons.t_medias``
* Mise en place de fonctions SQL et de vues permettant d'alimenter la Synthèse de GeoNature à partir des données des sous-modules des protocoles de suivi (#14)
* Ajout d'une commande d'installation d'un sous-module (``flask monitoring install <module_dir_config_path> <module_code>``)
* Ajout d'une commande de suppression d'un sous-module (``remove_monitoring_module_cmd(module_code)``)
* Documentation de l'installation et de la configuration d'un sous-module de protocole de suivi

* Des exemples de sous-modules sont présents [ici](https://github.com/PnCevennes/protocoles_suivi/)
