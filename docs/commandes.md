# Liste des commandes

Toutes les commandes s'exécutent avec le venv de GeoNature activé :

```sh
source ~/geonature/backend/venv/bin/activate
```

## Installer un sous-module

```sh
geonature monitorings install <module_code>
```

Voir [Installation d'un sous-module](/?id=installation-dun-sous-module).

## Mettre à jour les nomenclatures

Ajoute ou met à jour des nomenclatures en base de données à partir du fichier `nomenclature.json` de la configuration du sous-module (voir le fichier exemple `contrib/test/nomenclature.json`).

```sh
geonature monitorings add_module_nomenclature <module_code>
```

## Mettre à jour les objets de permissions

Ajoute les objets de permissions définis par le paramètre `permission_objects` du fichier `module.json` (à utiliser par exemple après l'ajout d'un niveau groupe de sites). La mise à jour correspond uniquement à un ajout d'objets de permissions : les suppressions doivent être réalisées manuellement.

```sh
geonature monitorings update_module_available_permissions               # tous les sous-modules
geonature monitorings update_module_available_permissions <module_code> # un seul sous-module
```

## Mettre à jour les vues SQL (synthèse et exports)

Ré-exécute les fichiers SQL de la vue de synthèse (`synthese.sql`) et des exports CSV (`exports/csv/`).

```sh
geonature monitorings process_sql               # tous les sous-modules
geonature monitorings process_sql <module_code> # un seul sous-module
```

## Activer ou mettre à jour l'import

Rend le sous-module disponible comme destination dans le module Import, ou répercute dans `gn_imports.bib_fields` les modifications des champs additionnels après une mise à jour de sa configuration. Le sous-module doit être installé et configuré au préalable. Voir [Import de données](import.md).

```sh
geonature monitorings process_import <module_code>
```

## Supprimer un sous-module

La suppression d'un sous-module n'est possible qu'en l'absence de données associées.

```sh
geonature monitorings remove <module_code>
```

## Mettre à jour la synthèse

Lit la vue de synchronisation liée au sous-module et synchronise les données dans la synthèse (insertion et mise à jour uniquement).

```sh
geonature monitorings synchronize_synthese <module_code>
```

L'option `--offset` (100 par défaut) définit le nombre de données insérées à chaque itération.
