Intégration des données dans la synthèse
########################################

La vue pour la synthèse
***********************

Pour les modules de type ``Site`` -> ``Visite`` -> ``Observation``
==================================================================

- Copier le fichier ``data/synthese_svo.sql`` dans ``<repertoire_sous_module>/synthese.sql``.

  - Ce script SQL sera exécuté automatiquement à l'installation du module (voir le paragraphe ``data/update_views.sh`` pour le jouer à la demande).
  - Cette vue peut être personalisée pour chaque module, on peut notamment :
  
    - mettre des valeurs présentes dans les table de complément (champs spécifiques) et qui peuvent alimenter des champs de la synthèse
    - donner des valeurs plus spécifique au module pour les champs de type nomenclature (la plupart sont en commentaires dans la vue) 

  - À la configuration du sous-module (page du sous-module, cliquer sur ``éditer le module``), activer la synthèse.

Au besoin, si des données sont déjà présentes, appuyer sur ``Mettre à jour la synthèse`` (attention cela peut prendre du temps). Cette action met à jour la synthèse pour tout le module.

La synthèse est mise à jour pour toutes les observations concernées par une création/modification d'un site, d'une visite ou d'une observation.

Pour les autres types de module
===============================

- Adapter la vue
- Ajouter ``"synthese_object": "visit"`` si le module s'arrête au niveau des visites

  - par défaut il est défini à ``observation``
  - cela permet de renseigner la table ``gn_synthese.t_sources`` (et de créer le lien dans la synthèse vers la module monitoring qui a généré la ligne de la synthèse)


Mettre à jour les vues pour la synthèse
***************************************

Tous les fichiers de vue pour la synthèse peuvent être re-exécutés avec la commande :

- ``data/update_views.sh <chemin absolu vers geonature>`` (tous les modules)
- ``data/update_views.sh <chemin absolu vers geonature> <module_code>`` (un seul module)


Mettre à jour la synthèse après une intégration massive de données
******************************************************************

Deux options:

- `SQL` : exécuter la commande: 
```
SELECT SELECT gn_synthese.import_row_from_table('id_module', '<id_du module>', 'gn_monitoring.<nom de la vue>')
```

- `frontend` : sur la page du module (en mode admin), appuyer sur le boutton `mettre à jour la synthèse`