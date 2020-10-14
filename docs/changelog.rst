# Changelog

0.2.0 (Unreleased)
------------------

Nécessite la version 2.5.0 de GeoNature minimum.

TODO : A mettre à jour dans manifest.toml avant release.

**Nouveautés**

* Ajout de la notion de groupes de sites (encore un peu jeune)
* Simplification de la procédure pour mettre les données dans la synthèse(un fichier à copier, un boutton à cocher et possibilité de customizer la vue pour un sous-module).
* Passage de la complexité des méthodes de mise en base des données et de gestion des relation par liste d'``id`` (observateurs, jdd du module, correlations site module) vers le module `Utils_Flask_SQLA` (amélioration de la méthode from_dict en mode récursif qui accepte des listes d'`id` et les traduit en liste de modèles) *(principalement dans `backend/monitoring/serializer.py`)*
* Possibilité de renseigner le JDD à chaque visite (#30)
* Possibilité pour les administrateurs d'associer les JDD à un sous-module directement depuis l'accueil du sous-module (#30)
* Possibilité de créer des groupes de sites (#24)
* Possibilité de créer une visite directement après la création d'un site, et d'une observation directement après la création d'une visite (#28)
* Redirection sur sa page de détail après la création d'un objet, plutôt que sur la liste (#22)
* Mise à jour du composant de gestion et d'affichage des médias
* Ajout d'un composant de liste modulable (``datalist``) pouvant interroger une API, pouvant être utilisé pour les listes de taxons, d'observateurs, de jdd, de nomenclatures, de sites, de groupes de sites, etc... (#44)
* Liste des observations : ajout d'un paramètre permettant d'afficher le nom latin des taxon observés (#36)
* Suppression du fichier ``custom.json`` pour gérer son contenu dans les nouveaux champs de la table ``gn_monitoring.t_module_complements`` (#43)
* Clarification et remplacement des ``module_path`` et ``module_code`` (#40)

**Corrections**

* Renseignement de la table ``gn_synthese.t_sources`` à l'installation (#33)
* Passage du commentaire de la visite en correspondance avec le champs ``comment_context`` de la Synthèse, dans la vue ``gn_monitoring.vs_visits`` (#31)
* Remplissage de la table ``gn_commons.bib_tables_location`` pour les tables du schémas ``gn_monitoring`` si cela n'a pas été fait par GeoNature (#27)
* Corrections et optimisations diverses du code et de l'ergonomie

**Notes de version**

Si vous mettez à jour le module depuis la vers 0.1.0 :

* Exécuter le script SQL de mise à jour de la BDD : ``data/migrations/0.1.0to0.2.0.sql`` (/!\ à renommer avant release !)
* Exécuter ``update_views.sh`` ???
* Renseigner les nouveaux champs de ``gn_monitoring.t_module_complements`` ?
* TOCHECK : Des modifications obligatoires à appliquer dans les fichiers JSON de configuration des modules ?

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
