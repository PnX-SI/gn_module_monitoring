# Changelog

0.1.1 (Unreleased)

**Corrections**

* Renseignement de la table `gn_synthese.t_source` à l'installation

0.1.0 (2020-06-30)
------------------

Première version fonctionelle du module Monitoring de GeoNature

**Fonctionnalités**

* Génération dynamique de sous-modules de gestion de protocoles de suivi
* Saisie et consultation de sites, visites et observations dans chaque sous-module
* Génération dynamique des champs spécifiques à chaque sous-module au niveau des sites, visites et observations (à partir de configurations json et basé sur le composant ``DynamicForm`` de GeoNature)
* Ajout de tables complémentaires pour étendre les tables ``t_base_sites`` et ``t_base_visits`` du schema ``gn_monitoring`` permettant de stocker dans un champs de type ``jsonb`` les contenus des champs dynamiques spécifiques à chaque sous-module
* Ajout de médias locaux ou distants (images, PDF, ...) sur les différents objets du module, stockés dans la table verticale ``gn_commons.t_medias``
* Mise en place de fonctions SQL et de vues permettant d'alimenter la Synthèse de GeoNature à partir des données des sous-modules des protocoles de suivi (#14)
* Ajout d'une commande d'installation d'un sous-module (``flask monitoring install <module_dir_config_path> <module_path>``)
* Ajout d'une commande de suppression d'un sous-module (``remove_monitoring_module_cmd(module_path)``)
* Documentation de l'installation et de la configuration d'un sous-module de protocole de suivi

* Des exemples de sous-modules sont présent [ici](https://github.com/PnCevennes/protocoles_suivi/)
