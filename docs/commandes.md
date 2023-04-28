# Installer un module


```sh
geonature monitorings install <mon_chemin_absolu_vers_mon_module> <mon_module_code>
```

# Mettre à jour la nommenclature

Ajoute ou met à jour des nomenclatures en base de données à partir du
fichier `nomenclature.json` de la config du module (voir le fichier
exemple `contrib/test/nomenclature.json`)

```sh
geonature monitorings add_module_nomenclature <mon_module_code>
```

# Mettre à jour les objets de permissions

La mise à jour correspond pour le moment uniquement à un ajout d'objet
de permission.

Les suppressions doivent être réalisées manuellement.

```sh
geonature monitorings update_permission_objects <mon_module_code>
```

# Supprimer un module

La suppression d'un module n'est possible qu'en cas d'absence de
données associées.

```sh
geonature monitorings remove <mon_module_code>
```

# Mettre à jour la synthese

Cette commande lit la vue de synchronisation liée au module et
synchronise les données dans la synthèse (insertion et mise à jour
uniquement).

```sh
geonature monitorings synchronize_synthese <module_code>>
```
