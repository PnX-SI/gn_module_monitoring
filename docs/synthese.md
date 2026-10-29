# Intégration des données dans la synthèse

L'intégration des données d'un sous-module dans la synthèse de GeoNature repose sur une vue SQL définie pour chaque sous-module.

## Pour les sous-modules de type `Site` → `Visite` → `Observation`

1. Copier le fichier `data/synthese_svo.sql` dans `<repertoire_sous_module>/synthese.sql`.
   - Ce script SQL sera exécuté automatiquement à l'installation du sous-module (utiliser la commande `geonature monitorings process_sql` pour le jouer à la demande).
2. Personnaliser la vue si besoin. On peut notamment :
   - utiliser des valeurs présentes dans les tables de complément (champs spécifiques) pour alimenter des champs de la synthèse ;
   - donner des valeurs plus spécifiques au sous-module pour les champs de type nomenclature (la plupart sont en commentaires dans la vue).
3. À la configuration du sous-module (page du sous-module, bouton `Éditer le module`), activer la synthèse.

> [!WARNING]
> Les colonnes suivantes sont obligatoires pour assurer la synchronisation entre la vue et la synthèse :
>
> - `unique_id_sinp`
> - `ids_observers` : tableau d'`id_role`
> - `id_base_visit` (si ce niveau est utilisé par le sous-module)
> - `id_base_site` (si ce niveau est utilisé par le sous-module)
> - `id_observation` (si ce niveau est utilisé par le sous-module)
> - `id_sites_group` (si ce niveau est utilisé par le sous-module)

Au besoin, si des données sont déjà présentes, cliquer sur `Mettre à jour la synthèse` (attention, cela peut prendre du temps). Cette action met à jour la synthèse pour tout le sous-module.

La synthèse est ensuite mise à jour pour toutes les observations concernées par une création ou modification d'un site, d'une visite ou d'une observation.

## Pour les autres types de sous-modules

- Adapter la vue.
- Ajouter `"synthese_object": "visit"` si le sous-module s'arrête au niveau des visites :
  - par défaut, il est défini à `observation` ;
  - cela permet de renseigner la table `gn_synthese.t_sources` (et de créer le lien, dans la synthèse, vers le sous-module qui a généré la ligne).

## Mettre à jour les vues pour la synthèse et les exports

Tous les fichiers de vues pour la synthèse et les exports peuvent être ré-exécutés avec la commande :

```sh
geonature monitorings process_sql               # tous les sous-modules
geonature monitorings process_sql <module_code> # un seul sous-module
```

## Mettre à jour la synthèse après une intégration massive de données

Deux options :

- **En SQL**, exécuter la requête :

  ```sql
  SELECT gn_synthese.import_row_from_table('id_module', '<id_du_module>', 'gn_monitoring.<nom_de_la_vue>');
  ```

- **Depuis l'interface**, sur la page du sous-module (en mode admin), cliquer sur le bouton `Mettre à jour la synthèse`.
