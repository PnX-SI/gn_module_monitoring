# Tests E2E Playwright – recette des permissions

Recette de bout en bout des permissions du module Monitoring, exécutée contre une instance
GeoNature déjà démarrée (frontend + backend) avec le module installé.

```bash
cd e2e
npm install && npx playwright install chromium
npx playwright test                                   # toute la recette (~235 cas, 4 workers)
npx playwright test -g "D – scope 1"                  # un bloc action × scope
npx playwright test -g "Formulaire – marking"         # un contexte × type d'objet
npx playwright test tests/gestionnaire-sites.spec.ts  # gestionnaire de sites seulement
GN_WORKERS=2 npx playwright test                      # moins de workers (≤ nombre de comptes)
npx playwright test --ui                              # mode interactif
npx playwright show-report                            # rapport HTML (erreurs, captures, traces)
```

## Préparation de l'instance (une fois)

1. **Sous-modules de test**, installés depuis `contrib/test` et `contrib/test_indi` sous des codes
   dédiés, pour ne pas entrer en conflit avec les fixtures pytest du module (qui installent `test`
   et `test_indi` dans la même base) :
   ```bash
   cp -r contrib/test <media>/monitorings/e2e_test && cp -r contrib/test_indi <media>/monitorings/e2e_test_indi
   geonature monitorings install e2e_test && geonature monitorings install e2e_test_indi
   ```
   Le setup les configure s'ils ne le sont pas (jeu de données, listes d'observateurs et de
   taxons, type de site, affichage dans le menu).
2. **Comptes de test**, un par worker (`e2e.worker1` … `e2e.workerN`), avec l'environnement
   virtuel de GeoNature :
   ```bash
   python e2e/scripts/create_test_users.py --count 4 --password e2e-password
   ```
   Chaque compte est rattaché au même organisme que le rôle « collègue » (`--organisme`, -1 par
   défaut), membre de `Grp_en_poste` pour l'accès à GeoNature (ce groupe ne doit donner aucun droit
   sur les sous-modules E2E), et ajouté à la liste d'observateurs des sous-modules.
3. La liste de taxons des sous-modules (`GN_ID_LIST_TAXONOMY`, 100 par défaut) doit contenir des taxons.

Le setup Playwright (`tests/monitoring.setup.ts`) complète à chaque lancement : droits complets du
compte de préparation (admin) sur les sous-modules, droits de chaque compte sur `MONITORINGS`
(accès, groupes de sites, sites ; remis à cet état par chaque test, ceux du gestionnaire de
sites les faisant varier) et un **jeu de données par compte** dont il est acteur (au
scope 1/2 de création, seuls ces jeux sont proposés dans le formulaire de visite).

## Variables

| Variable | Défaut | Rôle |
|---|---|---|
| `GN_BASE_URL` / `GN_API_URL` | `http://127.0.0.1:4200` / `http://127.0.0.1:8000` | instance |
| `GN_WORKERS` | `4` | workers Playwright = comptes `e2e.worker<n>` utilisés |
| `GN_USER_PREFIX` / `GN_USER_PASSWORD` | `e2e.worker` / `e2e-password` | comptes testés |
| `GN_ADMIN_USER` / `GN_ADMIN_PASSWORD` | `admin` / `admin` | compte qui prépare les données et pose les permissions |
| `GN_ROLE_SAME_ORG` | `4` (agent) | rôle du même organisme que les comptes testés |
| `GN_ROLE_OTHER_ORG` | `9999` (admin-test-import) | rôle d'un autre organisme |
| `GN_MODULE` / `GN_MODULE_INDI` | `e2e_test` / `e2e_test_indi` | sous-modules de test |
| `GN_ID_DATASET`, `GN_ID_LIST_OBSERVER`, `GN_ID_LIST_TAXONOMY` | 1er JDD actif, `1`, `100` | configuration des sous-modules |

## Fonctionnement

- **Parallélisme** (`tests/fixtures.ts`) : chaque worker utilise son propre compte et fait varier
  ses propres permissions ; chaque test pose ses droits, crée ses données et les supprime à la fin.
  Les tests sont donc indépendants (`fullyParallel`).
- **Permissions** (`tests/permissions.ts`) : GeoNature n'expose pas d'API d'écriture des
  permissions ; les tests pilotent en HTTP l'admin Flask `/admin/permissions/permission/`
  (création pré-remplie via `?module_code=&code_object=&code_action=`, liste filtrée
  `flt0_rle_equals` / `flt1_module_equals`, suppression). Scope 3 = `scope` vide, scope 0 = pas
  de permission. `PermissionManager` n'écrit que les différences entre deux tests.
- **Données** (`tests/data.ts`) : créées via l'API `/monitorings/refacto/<module>/...` par le compte
  de préparation, avec un propriétaire (numérisateur, observateurs, inventeur, opérateur) = compte
  testé / collègue / autre organisme.
- **Matrice** (`tests/recette-permissions.spec.ts`, modèle dans `tests/recette.ts`) :
  - **R** : un objet de permission varie à la fois (les pages parentes restent lisibles).
    Liste = la ligne apparaît dans la liste du parent ; Formulaire = la page détail est servie (GET 200/403).
  - **C** : action à `scope` sur tous les objets. Formulaire = bouton « Ajouter » de l'onglet ;
    Liste = « + » d'une ligne parente. Création réelle quand autorisée.
  - **U** : Liste = icône d'édition de la ligne puis « Valider » ; Formulaire = « Éditer » puis
    « Valider » (PATCH, ou message « permissions » sans écriture).
  - **D** : Liste = corbeille de la ligne ; Formulaire = « Supprimer » du formulaire d'édition.
    On vérifie que le DELETE vise le bon objet.
  - **Sous-module** : R (liste des modules, page du sous-module), U (édition), E (bouton Téléchargements).
  - **Gestionnaire de sites** (`tests/gestionnaire-sites.spec.ts`, contexte `generic`) : accès depuis
    la liste des modules, puis R/C/U/D × scopes × liste/formulaire sur les groupes de sites et les sites,
    avec les droits du module MONITORINGS (`MONITORINGS_GRP_SITES`, `MONITORINGS_SITES`).
  - Règle attendue (`allowed()`) : scope 0 rien, 1 mes données, 2 mon organisme, 3 tout ; les
    observations et leurs détails héritent de la visite parente (toujours au compte testé).
- Pages ouvertes avec les `parents_path` que pose la navigation de l'application ; document neuf
  (`gotoFresh`) seulement après une écriture ; fonds de carte bloqués.
