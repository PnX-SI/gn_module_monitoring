# Changelog

0.1.0 (unreleased)
------------------

Première version fonctionelle du module Monitoring de GeoNature

**TOCHECK**

* Commande remove_monitoring_module_cmd() à indiquer dans le README ? TODO
* Lancer la commande d'alimentation de la Synthèse ? (automatique si vue existe et __SYNTHESE = true dans config.json du module)
* Table gn_monitoring.t_observation_details à virer ? (ça peut servir... pour les modules plus complexe)

**CHECKED**

* vues.sql basculé dans install_gn_module.py (https://github.com/PnX-SI/gn_module_monitoring/commit/05634743112e2ba9f0cd96d5d6c69d9db603a1f8). A virer de https://github.com/PnX-SI/gn_module_monitoring/blob/develop/install_db.sh#L21 ? ok
* https://github.com/PnX-SI/gn_module_monitoring/blob/develop/data/delete_synthese.sql à exécuter à l'installation ? Partie à basculer dans GN ? Voir https://github.com/PnX-SI/gn_module_monitoring/issues/14#issuecomment-639671708 dans le module
* config_custom.json à renommer custom.json dans le README ?


**Fonctionnalités**

* Génération dynamique de sous-modules de gestion de protocoles de suivi
* Saisie et consultation de sites, visites et observations dans chaque sous-module
* Génération dynamique des champs spécifiques à chaque sous-module au niveau des sites, visites et observations (à partir de configurations json et basé sur le composant ``DynamicForm`` de GeoNature)
* Ajout de tables complémentaires pour étendre les tables ``t_base_sites`` et ``t_base_visits`` du schema ``gn_monitoring`` permettant de stocker dans un champs de type ``jsonb`` les contenus des champs dynamiques spécifiques à chaque sous-module
* Mise en place de fonctions SQL et de vues permettant d'alimenter la Synthèse de GeoNature à partir des données des sous-modules des protocoles de suivi
* Ajout d'une commande d'installation du module ``flask monitoring install <module_dir_config_path> <module_path>``
* Documentation de l'installation et de la configuration d'un sous-module de protocole de suivi
