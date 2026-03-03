# Import de données protocolées en utilisant le module Import

Depuis la version 2.17.0 de GeoNature, un ensemble de fonctionnalités a été ajouté, permettant d'importer des données protocolées dans le module Monitoring.
    
Ce développement a été réalisé dans le cadre d’un financement de PATRINAT et du ministère de la Transition écologique, avec Natural Solutions en charge des travaux d'intégration dans le module Monitoring.


## Prérequis

- La version 2.17.0 de GeoNature

## Compatibilité avec les protocoles

- L'import permet, à ce jour, d'importer des sites, des visites et des observations.
- L'intégration de l'import Monitoring ne permet pas encore d'importer les groupes de sites. Des développements sont en cours.
- Les instructions en JavaScript utilisées pour paramétrer l'affichage ou non d'un champ pour une entité (site, visite, observation) ne sont pas encore prises en compte. Des développements sont en cours.

## Activation de l'import dans un protocole de suivi Monitoring

Pour pouvoir importer des données d'un protocole, il faut d'abord que ledit protocole soit configuré. Si ce n'est pas le cas, rendez-vous dans la section dédiée du protocole, accessible depuis le bouton `Éditer le module`.

Une fois le protocole configuré, il suffit de lancer la commande `geonature monitorings process_import <module_code>`.

## En cas de mise à jour du protocole

En cas de mise à jour du protocole, il faut relancer la commande suivante : `geonature monitorings process_import <module_code>`.