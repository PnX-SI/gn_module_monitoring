Création d'un sous-module
#########################

=========================
Création d'un sous-module
=========================

* `Structure d'un module`_
* `Configuration générale`_
* `Configuration des objets`_
* `Nomenclature`_
* `Installation du sous-module`_

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
