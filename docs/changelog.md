# CHANGELOG

## 1.1.0 (unreleased)

Nécessite GeoNature 2.16.0 (ou plus)

**🚀 Nouveautés**
- Ajout de la gestion des individus pour les protocoles de suivi de type CMR, dans le cadre d'une prestation de la Société Herpétologique de France
  - Détail de la réalisation : #213. (#259, #402 par @mvergez, @andriacap, @amandine-sahl)
  - Ajout d'une documentation pour l'ajout des notions d'individus/marquage dans un sous-module et la configuration des marquages (docs/individuals.md)
  - Les individus/marquages sont des niveaux facultatifs qui peuvent être ajoutés (CMR) ou non en complément des niveaux groupes de sites, sites, visites et observations. Dans le cas où les individus sont activés, l'observation ne se rapporte plus à un taxon mais à un individu.
  - Le modèle est prévu pour qu'à terme, un même individu puisse être suivi par plusieurs protocoles/sous-modules
- Activation de la geolocalisation sur les cartes si le paramètre (`GEOLOCATION`) est activé dans la configuration globale de GeoNature (#371 by @pierre56)
- Complément de documentation sur les variables dynamiques (#439 by @marie-laure-cen, @amandine-sahl)


**🐛 Corrections**

- Synchronisation des données avec la synthèse lorsque le nom d'un module n'est pas en minuscule (#449 by @gildeluermoz)
- Correction de l'export des données quand la première colonne ne contient pas de valeur unique (#446 by @amandine-sahl)
- Compatibilité GN 2.16 et tests unitaires (#448, #452, #447 by @amandine-sahl)
- Erreur lorsqu'aucun item n'est trouvé pour une nomenclature


## 1.0.3 (06-05-25)

**🐛 Corrections**

- Correction des tris et filtres sur `id_inventor` sur la liste des sites (#423 by @amandine-sahl)
- Filtrer les routes géométries sur les propriétés spécifiques des modules (#422 by @amandine-sahl)
- Correction du filtre `nb_site` sur la route géométrie de `sites_group` (#422 by @amandine-sahl)
- Correction quand le paramètre de tri est inexistant dans la fonction sort + filtre des résultats lors du tri sur les observateurs (by @amandine-sahl)
- Correction de `formatLabelObservers` : retourne une valeur même quand null + simplification du code (by @amandine-sahl)
- Correction du spinner pendant le chargement des données (#415 by @andriacap, @amandine-sahl)
- Optimisation et amélioration des performances de la requête de récupération des modules de `get_module_by_id_base_site` (#433 by @andriacap)
- Correction d'appels multiples et croissants à la route `/module` depuis la page d'accueil (#425 by @amandine-sahl)
- Suppression de la fonction `filter_according_to_column_type_for_site` (#416 by @mathieu-roudaut-crea)
- Correction de l'exécution des scripts SQL avec des commentaires (#436 - #432)
- Synchronisation avec la synthèse : test si la colonne d'identification de l'objet n'existe pas une erreur est loguée coté backend mais non transmise au frontend (#436 - #432)
- Ajout de tests automatisés avec support de Debian 12 (#423 by @amandine-sahl)

## 1.0.2 (2025-03-14)

**🐛 Corrections**

- Optimisation de la récupération du CRUVED lors de la sérialisation des enfants lorsque l'utilisateur a une portée de 3 (#412)
- Correction des filtres des propriétés spécifiques de type nomenclature multiple (#412)
- Correction de la génération de la configuration d'un module (#399, #403, #405)

## 1.0.1 (2025-01-17)

**🐛 Corrections**

- Réduction du nombre d'appels des objets pour améliorer les performances de chargement des pages (#404, par @amandine-sahl)
- Correction de dysfonctionnement de l'enchainement des saisies (#396, #401, par @unjambonakap, @gildeluermoz, @amandine-sahl)
- Correction de la requête de synthèse du sous-module contrib/test (#350, par @marie-laure-cen,  @amandine-sahl)

## 1.0.0 (2024-12-13)

Nécessite GeoNature 2.15.0 (ou plus)

**🚀 Nouveautés**

- Les sites (et groupes de sites) peuvent désormais être utilisés dans plusieurs protocoles (sous-modules) (#117)
  - Un gestionnaire de sites permet de gérer les sites (et groupes de sites) globalement et non plus uniquement à l'intérieur de chaque sous-module
  - Chaque site est associé à un ou plusieurs types de sites
  - Un gestionnaire des types de sites est disponible dans le module "Admin" de GeoNature
  - Des champs additionnels peuvent être définis pour chaque type de site pour pouvoir décrire des sites globalement, et pas uniquement par protocole
  - Chaque sous-module est associé à un ou plusieurs type de site pour définir les sites qui seront proposés dans le sous-module
  - Le modèle de données a évolué pour pouvoir associer un site à plusieurs types et un sous-module à plusieurs types de sites (suppression du champs `id_nomenclature_type_site`)
  - Le modèle de données a évolué pour pouvoir associer un groupe de sites à plusieurs sous-modules
  - On distingue les permissions des utilisateurs dans chaque sous-module (protocole) sur chaque type d'objets (groupes de sites, sites et visites) et leurs permissions globales sur ces objets au niveau de tout le module. Pour qu'un utilisateur puisse consulter, ajouter ou modifier des groupes de sites ou des sites depuis le gestionnaire de sites, il faut lui ajouter des permissions globales sur ces objets.
- Ajout de la prise en compte des portées au niveau des permissions (#92)
- Ajout d'un champ `observers_txt` au niveau de la table des visites (#106)
- Possibilité de définir plusieurs types de géométrie pour les sites d'un sous-module (#136)
- Ajout de triggers de répercussion dans la Synthèse des données supprimées dans un sous-module de Monitoring (#286)
- Ajout de tests unitaires
- Suppression des commandes `process_csv` et `process_all` qui sont remplacées par la commande `process_sql` (#244)
- [process_sql] Ajout d'un controle de conformité des fichiers qui ne peuvent pas contenir les commandes SQL suivantes : INSERT, DELETE, UPDATE, EXECUTE, TRUNCATE, ALTER, GRANT, COPY, PERFORM, CASCADE
- Bascule de la table `t_observations` dans le cœur de GeoNature (#271)

**🐛 Corrections**

- Correction d'une erreur silencieuse lors de la synchronisation avec la synthèse (liée à l'absence de la vue de synchro ou d'un champs obligatoire) (#286)
- Mise à jour de SQLAlchemy version 1.3 à 1.4

**⚠️ Notes de version**

- Si vous installez le module sans être passés par la version 0.7.0, éxecuter le script `data\upgrade_modules_permissions.sql` pour transférer les permissions et supprimer les permissions disponibles (après avoir exécuté la commande `geonature monitorings update_module_available_permissions`).
- Si vous avez des modules installés, les éventuelles vues `synthese.sql` et `export_csv.sql` de vos sous-modules ne seront plus compatibles et bloqueront la migration. Il faut les supprimer avant la mise à jour et les recréer après mise à jour en répercutant les évolutions du modèle de données (#117)
- Si vous aviez défini la propriété `id_nomenclature_type_site` dans la configuration de vos sous-modules, celle-ci n'existe plus et peut être remplacée par `types_sites`. Exemple :
  ```
  "types_site": {
      "default": [
        {
          "id_nomenclature_type_site": 686
        }
      ],
      "hidden": true
    }
  ```
- Si vous le souhaitez, vous pouvez attribuer des permissions à vos utilisateurs au nouveau gestionnaire de sites et limiter les portées des permissions par objets et par sous-modules (https://github.com/PnX-SI/gn_module_monitoring?tab=readme-ov-file#permissions)
- Les données supprimées depuis le module ne l'étaient pas dans la synthèse. Vérifiez qu'il n'y a aucune donnée orpheline dans la synthèse, pour les supprimer ensuite si vous le souhaitez.

```sql
WITH monitoring_uuid AS (
	SELECT ms.uuid_base_site  AS unique_id_sinp
	FROM gn_monitoring.t_base_sites ms
	UNION
	SELECT mo.uuid_observation AS unique_id_sinp
	FROM gn_monitoring.t_observations mo
	UNION
	SELECT MOD.uuid_observation_detail  AS unique_id_sinp
	FROM gn_monitoring.t_observation_details mod
), monitoring_module AS (
	SELECT id_module
	FROM gn_commons.t_modules tm
	WHERE TYPE = 'monitoring_module'
)
SELECT *
FROM  gn_synthese.synthese s
JOIN  monitoring_module m
ON s.id_module = m.id_module
LEFT JOIN monitoring_uuid mu
ON s.unique_id_sinp = mu.unique_id_sinp
WHERE mu.unique_id_sinp IS NULL;
```

## 0.7.3 (2023-05-03)

**🐛 Corrections**

- Correction du selecteur des groupes de sites

## 0.7.2 (2023-02-27)

**🚀 Nouveautés**

- Mise à jour de la documentation sur l'alimentation de la synthèse et l'installation d'un sous-module
- Ajout des groupes de sites dans le sous-module de `test`

**🐛 Corrections**

- Erreur lors de l'installation du module (#284)
- Corrections des permissions (export PDF, groupes de sites)

## 0.7.1 (2023-12-05)

**🚀 Nouveautés**

- La gestion des permissions est définie pour chaque objet (module, site, visite) et l'objet ALL n'est plus pris en compte (#249). De fait les paramètres cruved des fichiers de configuration ainsi que permission object de `module.json` sont obsolètes.
- Ajout de tests

**🐛 Corrections**

- Export avec un filtre par jeux de données (#241)

## 0.7.0 (2023-08-23)

Nécessite la version 2.13.0 (ou plus) de GeoNature

**🚀 Nouveautés**

- Compatibilité avec GeoNature 2.13.0 et la refonte des permissions, en définissant les permissions disponibles du module (#232)
- Gestion des permissions disponibles des sous-modules lors de leur installation et création de la commande `update_module_available_permissions` permettant de les mettre à jour (#236)
- Récupération des permissions depuis le service `ModulesService` de GeoNature

**⚠️ Notes de version**

- Si elle est renseignée dans la configuration de vos sous-modules, la variable `permission_objects` est à déplacer du fichier `module.json` au fichier `config.json` de ces sous-modules
- Après mise à jour du module, utiliser la commande pour générer les permissions disponibles pour les sous-modules déjà installés

  ```
  geonature monitorings update_module_available_permissions
  ```

## 0.6.0 (2023-05-23)

Nécessite GeoNature version 2.12.0 (ou plus)

**🚀 Nouveautés**

- Utilisation de la gestion dynamique de la configuration de GeoNature (#224)
- Les dossiers de configuration des sous-modules sont déplacés du dossier `<gn_module_monitoring>/config/monitorings` vers le dossier `media/monitorings` de GeoNature. Cela permet d'homogéneiser et centraliser la configuration de GeoNature et de ses sous-modules, de permettre la dockerisation du module Monitoring et de simplifier sa mise à jour (#224)
- Installation des sous-modules en deux temps
- Passage de la documentation au format `markdown` (#227)
- Suppression du script obsolète `update_views.sh`
- Commande d'installation d'un sous-module : ajout de la liste des modules installés et disponibles

**⚠️ Notes de version**

- Veuillez déplacer les configurations des sous-modules déjà existants depuis le dossier `<gn_module_monitoring>/config/monitoring` vers le dossier `media` de GeoNature :

  ```
  cp -R ~/gn_module_monitoring/config/monitoring/* ~/geonature/backend/media/monitorings
  rm -R ~/geonature/backend/media/monitorings/generic
  ```

  Adapter cette commande si le répertoire `medias` de GeoNature est différent de l'exemple ci-dessus.
  Attention aux `s` à la fin de monitoring (le premier sans le deuxième avec).

- L'installation des sous-modules se fait désormais en deux temps :

      * Copie du répertoire de configuration
        ```sh
        cp <chemin vers le sous-module> <geonature>/backend/media/monitorings/<module_code>
        ```
      * Installation du sous-module avec la commande dédiée
        ```sh
        geonature monitorings install <module_code>
        ```

## 0.5.0 (2023-03-29)

Nécessite GeoNature version 2.12.0 (ou plus)

**🚀 Nouveautés**

- Compatibilité avec GeoNature 2.12 (Passage à la version 15 d'Angular et révision des permissions)
- Centralisation de la configuration du module dans le dossier de configuration de GeoNature
  - Pour le fichier de `<geonature>/config/monitorings_config.toml` (facultatif car non utilisé)
  - et le dossier de configuration des sous-modules `<geonature>/config/monitorings`
- Permissions : utilisation du décorateur de route classique `check_cruved_scope`
- Amélioration de l'affichage des images sur la page listant les sous-modules (#214)
- Remplacement du composant `datalist` par le composant `dataset` pour le champs de selection du JDD de la visite, dans la configuration générique des sous-modules

**🐛 Corrections**

- Correction de l'API `get_util_from_id_api` en traitant les `id` en `str` (#175)

**⚠️ Notes de version**

- L'utilisation du widget `datalist` pour les jeux de données est à proscrire. Si vous utilisez ce composant dans vos fichiers de configuration, il faut les modifier en remplaçant par le widget `dataset`.

```json
  "id_dataset": {
    "type_widget": "dataset",
    "attribut_label": "Jeu de données",
    "type_util": "dataset",
    "required": true,
    "module_code": "__MODULE.MODULE_CODE",
  },
```

## 0.4.1 (2023-02-05)

**🚀 Nouveautés**

- Configuration des exports pour rendre optionnelle la sélection du
  jeu de données avec le nouveau paramètre `filter_dataset` (#158)

**🐛 Corrections**

- Amélioration des performances du chargement des observations (#142)
- Correction du modèle "Observation détail" qui permet d'ajouter
  des informations sous le niveau observation

**⚠️ Notes de version**

Si vous souhaitez que les exports soient filtrables par jeux de données,
il faut rajouter le nouveau paramètre `filter_dataset` dans la variable
`export_csv`, définie à `true` au niveau de la configuration des modules
concernés (dans leur fichier `module.json`). Exemple :

```json
"export_csv": [
    { "label": "Format standard CSV", "type":"csv" , "method": "standard" , "filter_dataset": true},
    { "label": "Format analyses CSV", "type":"csv" , "method": "analyses" }
],
```

## 0.4.0 (2022-12-21)

Nécessite la version 2.11.0 (ou plus) de GeoNature.

**🚀 Nouveautés**

- Packaging du module (#190)
- Gestion de la base de données avec Alembic (#190)
- Améliorations du typage frontend

**🐛 Corrections**

- Correction du marqueur Leaflet non visible lors de la création d'un
  point sur la carte (#187)
- Peuplement du champs `gn_monitoring.t_module_complements.type` avec
  la valeur `monitoring_module` pour les sous-modules de Monitoring
  (#193)
- Correction de l'utilisation des modèles de TaxRef
- Suppression de l'usage de `MODULE_URL` dans la configuration du
  module (<https://github.com/PnX-SI/GeoNature/issues/2165>)

**⚠️ Notes de version**

Si vous mettez à jour le module, il vous faut passer à Alembic. Pour
cela, une fois la version 2.11 (ou plus) de GeoNature installée :

- Entrer dans le virtualenv :

```sh
source ~/geonature/backend/venv/bin/activate
```

- Installer la nouvelle version de Monitoring avec le paramètre
  `--upgrade-db=false` :

```sh
geonature install-gn-module --upgrade-db=false <path_to_monitoring> MONITORINGS
```

- Indiquer à Alembic que votre base de données est en version 0.3.0 :

```sh
geonature db stamp 362cf9d504ec                   # monitorings 0.3.0
```

- Mettre à jour la base de données en version 0.4.0 :

```sh
geonature db upgrade monitorings@head
```

## 0.3.0 (2022-11-02)

Nécessite la version 2.10.0 (ou plus) de GeoNature.

**🚀 Nouveautés**

- Compatibilité avec Angular version 12, mis à jour dans la version
  2.10.0 de GeoNature (#135)
- Ajout de la commande `synchronize_synthese` permettant de
  synchroniser les données d'un sous-module vers la Synthèse (#176)
- Tri de la liste des sous-modules par nom sur la page d'accueil du
  module (#182)
- Ajout des champs `altitude_min` et `altitude_max` dans les
  informations affichables au niveau des sites (`generic/site.json`)
  (#170)
- Calcul de la géometrie des groupes de sites basculé au niveau
  backend (avec la fonction `ST_ConvexHull` de PostGIS qui prend
  l'enveloppe convexe des sites du groupe - #149)
- Amélioration du style des informations sur les fiches des objets
  (#151)
- Ajout d'un paramètre `redirect_to_parent` au niveau de
  `observation.json` permettant de rediriger vers la fiche de la
  visite à la fin de la saisie en mode \"Enchainer les saisies\",
  plutôt que vers la fiche de l'observation (#152)
- Ajout de la commande `process_all` permettant de régénérer toute la
  configuration d'un sous-module quand il est déjà installé en base
  de données
- Possibilité de transmettre la valeur du code du module dans
  l'export (#168)

**🐛 Corrections**

- Correction de la hauteur aléatoire du container principal (#146)
- Correction du zoom sur un objet de la carte au clic sur l'objet
  dans la liste (#149)
- Correction de l'affichage des tooltips quand la géométrie est un
  polygone (#159)
- Correction de la transformation des chaines de caractère en date
  (#170)
- Suppression de l'alias `@librairies` (#178)

## 0.2.10 (2022-03-02)

Compatible avec GeoNature version 2.9.2 maximum.

**🐛 Corrections**

- Reprise de la config pour les champs de jeux de données et les
  observateurs
- Prise en compte du changement de l'api pour les jdd pour le choix
  des jdd de l'export

## 0.2.9 (2022-01-13)

Compatibilité avec GeoNature version 2.9.0 et plus.

**🐛 Corrections**

- Correction de la vue `gn_monitoring.synthese_svo.sql` permettant
  d'alimenter la Synthèse de GeoNature (#64)
- Reprise du composant de la liste déroulante de sélection des jeux de
  données, suite au passage à `ng-select2` dans GeoNature 2.9.0

## 0.2.8 (2021-12-10)

**🐛 Corrections**

- Suppression du trigger `tri_meta_dates_change_t_module_complements`
  dans le script d'installation du module (#118 et #120)
- Modification de la fonction contour des sites :
  - Un contour pour chaque groupe de sites
  - Prise en compte uniquement des sites visibles sur la carte (non
    filtrés) dans le calcul
- Complément des notes de version de la 0.2.7 (#119 par \@maximetoma)
- Les modules POPAmphibien et POPReptile ont été déplacés dans le
  dépot <https://github.com/PnCevennes/protocoles_suivi>

## 0.2.7 (2021-10-26)

**⚠️ Notes de version**

Si vous mettez à jour le module :

- Nouvelles commandes pour gérer et mettre à jour les exports `pdf` et
  `csv` pour un module si `module_code` est précisé ou pour tous les
  modules :

**🚀 Nouveautés POPAmphibien - POPReptile**

- A partir de la version de GeoNature 2.7.5, les commandes de gestion
  du module `monitorings` sont accessibles depuis la commande
  `geonature monitorings` une fois que l'on a activé le `venv`
- Nouvelles commandes :
  - `geonature monitorings process_export_pdf <?module_code>`
  - `geonature monitorings process_export_csv <?module_code>`
  - Pour gérer et mettre à jour les exports `pdf` et `csv` pour un
    module si `module_code` est précisé ou pour tous les modules
- Ajout des sous-modules POPAmphibien et POPReptile (idéalement à
  déplacer dans un autre dépôt)
- Possibilité de choisir la couleur du tableau pour les détails d'un
  objet (champs `color` dans le fichier `<object_type>.json`)
- Dans la partie map, possibilité de joindre les sites par des lignes
  pour former automatiquement une aire et calculer sa superficie
  - (si le nombre des points est supérieur à 2)
  - configurable depuis l'édition du module ([dessin des groupe de
    site]{.title-ref})
- Possibilité de choisir l'icône du module dans le menu depuis
  l'édition du module
- Export PDF configurables
  - Bouton accessible depuis les détails
- Export CSV configurables
  - Bouton accessible depuis les détails
  - Modale pour choisir le JDD concerné par l'export

**🐛 Corrections**

- Rechargement de la configuration quand on modifie le module par le
  formulaire d'édition

**⚠️ Notes de version**

Si vous mettez à jour le module :

- Pour mettre à jour la base de données, il faut exécuter le fichier
  `data/migration/migration_0.2.6_0.2.7.sql`
- Les exports nécessitent l'installation du module html2canvas. Il
  peut être nécessaire de mettre à jour les modules js en suivant la
  procédure suivante :

```sh
cd path_to_geonature/frontend
npm install external_modules/monitorings/frontend --no-save
```

## 0.2.6 (2021-07-23)

Compatible avec GeoNature à partir de sa version 2.6.2 (dont GeoNature
2.8).

**🚀 Nouveautés**

- Assets déplacés dans le dossier `static`
  (`backend/static/external_assets/monitorings/`) de GeoNature (#102)
- Dans les listes d'objets, ajout d'un bouton plus pour accéder
  directement à la création d'un enfant (#97)
  - par exemple depuis la liste des sites on peut accéder
    directement à la création d'une nouvelle visite

**🐛 Corrections**

- Chargement des commandes Flask

**⚠️ Notes de version**

- L'emplacement des images des modules (dans la page d'accueil qui
  permet de choisir un module) change.

Elles sont placées dans
`backend/static/external_assets/monitorings/assets`, l'avantage est
qu'il n'est plus nécessaire de rebuild le frontend à l'installation
d'un sous module.

- Pour les mettre à jour, veuillez exécuter la commande suivante :

```sh
source /home/`whoami`/geonature/backend/venv/bin/activate
export FLASK_APP=geonature
flask monitorings process_img
```

ou bien à partir de GeoNature 2.7.3 :

```sh
source /home/`whoami`/geonature/backend/venv/bin/activate
export FLASK_APP=geonature
geonature monitorings process_img
```

## 0.2.5 (2021-07-12)

**🐛 Corrections**

Problème de route frontend (#100)

## 0.2.4 (2021-06-15)

**🐛 Corrections**

- Problème de chainage des saisies
- Configuration de l'affichage des taxons `lb_nom` pris en compte

Version minimale de GeoNature nécessaire : 2.6.2

## 0.2.3 (2021-04-01)

Version minimale de GeoNature nécessaire : 2.5.5

**🐛 Corrections**

- Problème d'héritage des permissions (#78)

**⚠️ Notes de version**

Si vous mettez à jour le module :

- Suivez la procédure classique de mise à jour du module
  (`docs/MAJ.rst`)

## 0.2.2 (2021-03-22)

- Version minimale de GeoNature nécessaire : 2.5.5

**🚀 Nouveautés**

- Gestion des permissions par objet (site, groupe de site, visite,
  observation)
- Interaction carte liste pour les groupes de site

**🐛 Corrections**

- Affichage des tooltips pour les objets cachés #76

**⚠️ Notes de version**

Si vous mettez à jour le module :

- Pour mettre à jour la base de données, il faut exécuter le fichier
  `data/migration/migration_0.2.1_0.2.2.sql`
- Suivez la procédure classique de mise à jour du module
  (`docs/MAJ.rst`)
- Nettoyer des résidus liées à l'ancienne versions :

```sh
cd /home/`whoami`/geonature/frontend
npm uninstall test
npm ci /home/`whoami`/gn_module_monitoring/frontend/ --no-save
```

## 0.2.1 (2021-01-14)

- Version minimale de GeoNature nécessaire : 2.5.5

**🚀 Nouveautés**

- Amélioration des groupes de sites (#24)
- Possibilité de charger un fichier GPS ou GeoJSON pour localiser un
  site (#13)
- Alimentation massive de la synthèse depuis les données historiques
  d'un sous-module de suivi (#38)
- Pouvoir définir des champs _dynamiques_, dont les attributs peuvent
  dépendre des valeurs des autres composants (pour afficher un
  composant en fonction de la valeur d'autres composants). Voir les
  exemples dans le sous-module `test`
- Pouvoir definir une fonction `change` dans les fichiers
  `<object_type>.json` qui est exécutée à chaque changement du
  formulaire.
- Champs data JSONB dans `module_complement`
- Gestion des objets qui apparraissent plusieurs fois dans `tree`. Un
  objet peut avoir plusieurs [parents]{.title-ref}
- Améliorations grammaticales et possibilité de genrer les objets
- Choisir la possibilité d'afficher le bouton saisie multiple
- Par defaut pour les sites :
  - `id_inventor` = `currentUser.id_role` si non défini
  - `id_digitizer` = `currentUser.id_role` si non défini
  - `first_use_date` = `<date courante>` si non défini

**🐛 Corrections**

- Amélioration du titre (lisibilité et date francaise)
- Correction de la vue alimentant la synthèse
- Ajout du champs `base_site_description` au niveau de la
  configuration générique des sites (#58)

**⚠️ Notes de version**

Si vous mettez à jour le module :

- Pour mettre à jour la base de données, il faut exécuter le fichier
  `data/migration/migration_0.2.0_0.2.1.sql`
- Pour mettre à jour la base de données, exécutez le fichier
  `data/migration/migration_0.2.0_0.2.1.sql`
- Suivez la procédure classique de mise à jour du module
  (`docs/MAJ.rst`)
- Les fichiers `config_data.json`, `custom.json`, et/ou la variable
  [data]{.title-ref} dans `config.json` ne sont plus nécessaires et
  ces données sont désormais gérées automatiquement depuis la
  configuration.

## 0.2.0 (2020-10-23)

Nécessite la version 2.5.2 de GeoNature minimum.

**🚀 Nouveautés**

- Possibilité de renseigner le JDD à chaque visite
  ([#30](https://github.com/PnX-SI/gn_module_monitoring/issues/30))
- Possibilité pour les administrateurs d'associer les JDD à un
  sous-module directement depuis l'accueil du sous-module
  ([#30](https://github.com/PnX-SI/gn_module_monitoring/issues/30))
- Possibilité de créer des groupes de sites (encore un peu jeune)
  ([#24](https://github.com/PnX-SI/gn_module_monitoring/issues/24))
- Possibilité de créer une visite directement après la création d'un
  site, et d'une observation directement après la création d'une
  visite
  ([#28](https://github.com/PnX-SI/gn_module_monitoring/issues/28))
- Redirection sur sa page de détail après la création d'un objet,
  plutôt que sur la liste
  ([#22](https://github.com/PnX-SI/gn_module_monitoring/issues/22))
- Mise à jour du composant de gestion et d'affichage des médias
- Ajout d'un composant de liste modulable (`datalist`) pouvant
  interroger une API, pouvant être utilisé pour les listes de taxons,
  d'observateurs, de jdd, de nomenclatures, de sites, de groupes de
  sites, etc...
  ([#44](https://github.com/PnX-SI/gn_module_monitoring/issues/44))
- Liste des observations : ajout d'un paramètre permettant
  d'afficher le nom latin des taxons observés
  ([#36](https://github.com/PnX-SI/gn_module_monitoring/issues/36))
- Simplification de la procédure pour mettre les données dans la
  synthèse (un fichier à copier, un bouton à cocher et possibilité de
  customiser la vue pour un sous-module)
- Passage de la complexité des méthodes de mise en base des données et
  de gestion des relation par liste d'`id` (observateurs, jdd du
  module, correlations site module) vers le module
  [Utils\_Flask\_SQLA]{.title-ref} (amélioration de la méthode
  `from_dict` en mode récursif qui accepte des listes d'`id` et les
  traduit en liste de modèles), (principalement dans
  `backend/monitoring/serializer.py`)
- Suppression du fichier `custom.json` pour gérer son contenu dans les
  nouveaux champs de la table `gn_monitoring.t_module_complements`
  ([#43](https://github.com/PnX-SI/gn_module_monitoring/issues/43))
- Clarification et remplacement des `module_path` et `module_code`
  ([#40](https://github.com/PnX-SI/gn_module_monitoring/issues/40))

**🐛 Corrections**

- Amélioration des modèles SLQA pour optimiser la partie sérialisation
  ([#46](https://github.com/PnX-SI/gn_module_monitoring/issues/46))
- Renseignement de la table `gn_synthese.t_sources` à l'installation
  ([#33](https://github.com/PnX-SI/gn_module_monitoring/issues/33))
- Passage du commentaire de la visite en correspondance avec le champs
  `comment_context` de la Synthèse, dans la vue
  `gn_monitoring.vs_visits`
  ([#31](https://github.com/PnX-SI/gn_module_monitoring/issues/31))
- Remplissage de la table `gn_commons.bib_tables_location` pour les
  tables du schéma `gn_monitoring` si cela n'a pas été fait par
  GeoNature
  ([#27](https://github.com/PnX-SI/gn_module_monitoring/issues/27))
- Corrections et optimisations diverses du code et de l'ergonomie
- Corrections de la documentation et docstrings (par \@jbdesbas)

**⚠️ Notes de version**

Si vous mettez à jour le module depuis la version 0.1.0 :

- Les fichiers `custom.json` ne sont plus utiles (la configuration
  spécifique à une installation (liste utilisateurs, etc..) est
  désormais gérée dans la base de données, dans la table
  `gn_monitoring.t_module_complements`)
- Dans les fichiers `config.json`, la variable `data` (pour précharger
  les données (nomenclatures, etc..)) est désormais calculée depuis la
  configuration.
- Pour mettre à jour la base de données, il faut exécuter le fichier
  `data/migration/migration_0.1.0_0.2.0.sql`
- Suivez la procédure classique de mise à jour du module
  (`docs/MAJ.rst`)

## 0.1.0 (2020-06-30)

Première version fonctionelle du module Monitoring de GeoNature.
Nécessite la version 2.4.1 de GeoNature minimum.

**Fonctionnalités**

- Génération dynamique de sous-modules de gestion de protocoles de
  suivi
- Saisie et consultation de sites, visites et observations dans chaque
  sous-module
- Génération dynamique des champs spécifiques à chaque sous-module au
  niveau des sites, visites et observations (à partir de
  configurations json et basé sur le composant `DynamicForm` de
  GeoNature)
- Ajout de tables complémentaires pour étendre les tables
  `t_base_sites` et `t_base_visits` du schema `gn_monitoring`
  permettant de stocker dans un champs de type `jsonb` les contenus
  des champs dynamiques spécifiques à chaque sous-module
- Ajout de médias locaux ou distants (images, PDF, ...) sur les
  différents objets du module, stockés dans la table verticale
  `gn_commons.t_medias`
- Mise en place de fonctions SQL et de vues permettant d'alimenter la
  Synthèse de GeoNature à partir des données des sous-modules des
  protocoles de suivi (#14)
- Ajout d'une commande d'installation d'un sous-module
  (`flask monitoring install <module_dir_config_path> <module_code>`)
- Ajout d'une commande de suppression d'un sous-module
  (`remove_monitoring_module_cmd(module_code)`)
- Documentation de l'installation et de la configuration d'un
  sous-module de protocole de suivi
- Des exemples de sous-modules sont présents
  [ici](https://github.com/PnCevennes/protocoles_suivi/)
