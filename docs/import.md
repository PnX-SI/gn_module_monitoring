# Import de données protocolées en utilisant le module Import

Depuis la version 2.17.0 de GeoNature, un ensemble de fonctionnalités a été ajouté, permettant d'importer des données de sites, visites et/ou observations depuis des fichiers CSV dans le module Monitoring, en s'appuyant sur le module Import de GeoNature.
    
Ce développement a été réalisé dans le cadre d’un financement de PatriNat et du ministère de la Transition écologique, avec Natural Solutions et le Parc national des Ecrins en charge des travaux d'intégration dans le module Monitoring.


## Prérequis

- Disposer de la version 2.17.0 (ou plus) de GeoNature

## Compatibilité avec les protocoles

- L'import permet, à ce jour, d'importer des sites, des visites et des observations.
- L'intégration de l'import Monitoring ne permet pas encore d'importer les groupes de sites. Des développements sont en cours.
- Les instructions en JavaScript utilisées pour paramétrer l'affichage ou non d'un champ pour une entité (site, visite, observation) ne sont pas encore prises en compte. Des développements sont en cours.

## Activation de l'import dans un protocole de suivi Monitoring

Pour pouvoir importer des données d'un sous-module Monitoring, il faut d'abord que ledit sous-module soit configuré. Si ce n'est pas le cas, rendez-vous dans la section dédiée du sous-module, accessible depuis le bouton `Éditer le module`.

Une fois le sous-module configuré, il suffit de lancer la commande `geonature monitorings process_import <module_code>`.

Une destination d'import est créée pour chaque sous-module. 

Les utilisateurs qui peuvent importer des données dans un sous-module Monitoring sont celles qui ont des permissions de Création sur ce sous-module ainsi que sur le module Import.

Pour en savoir plus sur le fonctionnement du module Import, voir sa documentation sur https://docs.geonature.fr/user-manual.html#import

## En cas de mise à jour du sous-module

En cas de mise à jour de la configuration du sous-module, il faut relancer la commande suivante pour répercuter les modifications de la définition des champs additionnels des sites, visites et observations dans la table `gn_imports.bib_fields` : `geonature monitorings process_import <module_code>`.