import { Page, Locator, Response, expect } from '@playwright/test';
import { fullCrud, PermissionSpec, Action, Scope } from './permissions';
import { TestData, MODULE, MODULE_INDI, OBJECTS, ObjectType, moduleOf } from './data';
import { MONITORING_URL, uniqueName } from './helpers';

/**
 * Propriétaires des données, pour distinguer les scopes :
 * - me : le compte testé du worker (scope 1 « mes données »)
 * - colleague : un autre rôle du même organisme (scope 2 « mon organisme »)
 * - other : un rôle d'un autre organisme (seulement scope 3 « toutes les données »)
 */
export type Owner = 'me' | 'colleague' | 'other';
export const OWNERS: Owner[] = ['me', 'colleague', 'other'];
export const ROLE_SAME_ORG = Number(process.env.GN_ROLE_SAME_ORG ?? 4); // agent (organisme -1, comme les comptes e2e)
export const ROLE_OTHER_ORG = Number(process.env.GN_ROLE_OTHER_ORG ?? 9999); // admin-test-import (organisme 1)

export const SCOPES: Scope[] = [0, 1, 2, 3];

/** Objets de permission par sous-module de test. */
export const PERM_OBJECTS: Record<string, string[]> = {
  [MODULE]: ['MONITORINGS_MODULES', 'MONITORINGS_GRP_SITES', 'MONITORINGS_SITES', 'MONITORINGS_VISITES'],
  [MODULE_INDI]: ['MONITORINGS_MODULES', 'MONITORINGS_SITES', 'MONITORINGS_VISITES', 'INDIVIDUALS', 'MONITORINGS_MARKINGS'],
};

/** Hiérarchie / navigation de chaque type d'objet. */
export const TYPES: Record<
  ObjectType,
  {
    permObject: string;
    /** `parents_path` posé par la navigation de l'application sur la page détail */
    parentsPath: string[];
    /** type parent (null = page d'accueil du sous-module) */
    parent: ObjectType | null;
    /** onglet listant le type sur la page de son parent */
    tab: RegExp;
    /** formulaire du parent : bouton « Valider et saisir des <enfant> » */
    label: string;
    /** champ affiché en liste qui identifie la ligne (texte unique posé à la création) */
    rowField: string;
  }
> = {
  sites_group: { permObject: 'MONITORINGS_GRP_SITES', parentsPath: ['module'], parent: null, tab: /^Groupes de sites/, label: 'groupe de sites', rowField: 'sites_group_name' },
  site: { permObject: 'MONITORINGS_SITES', parentsPath: ['module', 'sites_group'], parent: 'sites_group', tab: /^Sites/, label: 'site', rowField: 'base_site_name' },
  visit: { permObject: 'MONITORINGS_VISITES', parentsPath: ['module', 'sites_group', 'site'], parent: 'site', tab: /^Visites/, label: 'visite', rowField: 'comments' },
  observation: { permObject: 'MONITORINGS_VISITES', parentsPath: ['module', 'sites_group', 'site', 'visit'], parent: 'visit', tab: /^Observations/, label: 'observation', rowField: 'comments' },
  observation_detail: { permObject: 'MONITORINGS_VISITES', parentsPath: ['module', 'sites_group', 'site', 'visit', 'observation'], parent: 'observation', tab: /^Observations détail/, label: 'détail d’observation', rowField: 'uuid_observation_detail' },
  individual: { permObject: 'INDIVIDUALS', parentsPath: ['module'], parent: null, tab: /^Individus/, label: 'individu', rowField: 'individual_name' },
  marking: { permObject: 'MONITORINGS_MARKINGS', parentsPath: ['module', 'individual'], parent: 'individual', tab: /^Marquages/, label: 'marquage', rowField: 'marking_code' },
};
export const OBJECT_TYPES = Object.keys(TYPES) as ObjectType[];

/**
 * Règle attendue : l'utilisateur peut-il agir (au scope donné) sur une donnée de `owner` ?
 * Les observations et leurs détails héritent de la visite parente (cf. has_instance_permission
 * backend) : leur parent appartenant toujours à l'utilisateur testé, elles sont accessibles dès le scope 1.
 */
export function allowed(type: ObjectType, scope: Scope, owner: Owner) {
  if (scope === 0) return false;
  if (scope === 3) return true;
  if (type === 'observation' || type === 'observation_detail') return true;
  return scope === 1 ? owner === 'me' : owner !== 'other';
}

/** Spécification de droits : tout à 3, sauf `action` = `scope` sur `objects` (tous les objets si absent). */
export function permissionsFor(module: string, action?: Action, scope?: Scope, objects?: string[]): PermissionSpec {
  const spec = fullCrud(PERM_OBJECTS[module]);
  if (action === undefined) return spec;
  for (const code of objects ?? PERM_OBJECTS[module].filter((o) => o !== 'MONITORINGS_MODULES')) {
    if (spec[code]) spec[code][action] = scope;
  }
  return spec;
}

/**
 * Droits du compte testé sur MONITORINGS (gestionnaire de sites) : accès au module, groupes de
 * sites / sites (certaines routes des sous-modules vérifient les droits sur MONITORINGS) et
 * lecture des types de site. Tout à 3, sauf `action` = `scope` sur `objects` (groupes de sites
 * et sites si absent).
 */
export const GENERIC_OBJECTS = ['MONITORINGS_GRP_SITES', 'MONITORINGS_SITES'];
export function monitoringsSpec(action?: Action, scope?: Scope, objects: string[] = GENERIC_OBJECTS): PermissionSpec {
  const spec: PermissionSpec = {
    ALL: { R: 3 },
    MONITORINGS_GRP_SITES: { C: 3, R: 3, U: 3, D: 3 },
    MONITORINGS_SITES: { C: 3, R: 3, U: 3, D: 3 },
    TYPES_SITES: { R: 3 },
  };
  if (action === undefined) return spec;
  for (const code of objects) spec[code][action] = scope;
  return spec;
}

const query = (parentsPath: string[]) => (parentsPath.length ? `?${parentsPath.map((p) => `parents_path=${p}`).join('&')}` : '');

/** URL front de la page détail, telle que produite par la navigation de l'application. */
export const detailUrl = (type: ObjectType, id: number) =>
  `${MONITORING_URL}/object/${moduleOf(type)}/${type}/${id}${query(TYPES[type].parentsPath)}`;

/** URL front de la page d'accueil d'un sous-module (listes des objets de 1er niveau). */
export const moduleUrl = (module: string) => `${MONITORING_URL}/object/${module}/sites_group`;

/** Page listant `type` : page d'accueil du sous-module ou page détail du parent. */
export const listUrl = (type: ObjectType, parentId?: number) => {
  const parent = TYPES[type].parent;
  return parent ? detailUrl(parent, parentId!) : moduleUrl(moduleOf(type));
};

/** Objet de test, et ce qu'il faut pour le retrouver dans une liste. */
export type Entry = { owner: Owner; id: number; listUrl: string; rowText: string };

export function roleOf(owner: Owner, me: number) {
  return { me, colleague: ROLE_SAME_ORG, other: ROLE_OTHER_ORG }[owner];
}

/**
 * Crée le parent (à l'utilisateur testé) sous lequel seront créés les objets de `type`
 * (pour un détail d'observation : la visite).
 */
export async function seedParent(data: TestData, type: ObjectType): Promise<number | undefined> {
  switch (type) {
    case 'sites_group':
    case 'individual':
      return undefined;
    case 'site':
      return (await data.sitesGroup()).id_sites_group;
    case 'visit':
      return (await data.site({ idSitesGroup: (await data.sitesGroup()).id_sites_group })).id_base_site;
    case 'observation':
    case 'observation_detail': {
      const site = await data.site({ idSitesGroup: (await data.sitesGroup()).id_sites_group });
      // détail d'observation : l'observation (porteuse de l'appartenance) est créée par propriétaire
      return (await data.visit(site.id_base_site)).id_base_visit;
    }
    case 'marking':
      return (await data.individual()).id_individual;
  }
}

/**
 * Crée, sous un même parent, un objet de `type` par propriétaire. Pour un détail d'observation,
 * l'appartenance est celle de l'observation : une observation par propriétaire, chacune avec un détail.
 */
export async function seedEntries(data: TestData, type: ObjectType, owners: Owner[] = OWNERS): Promise<Entry[]> {
  const me = (await data.references()).idRole;
  const parentId = await seedParent(data, type);
  const entries: Entry[] = [];
  for (const owner of owners) {
    const role = roleOf(owner, me);
    const text = uniqueName(`${type}-${owner}`);
    let obj: Record<string, any>;
    let parent = parentId;
    switch (type) {
      case 'sites_group':
        obj = await data.sitesGroup({ owner: role, name: text });
        break;
      case 'site':
        obj = await data.site({ owner: role, name: text, idSitesGroup: parentId });
        break;
      case 'visit':
        obj = await data.visit(parentId!, { owner: role, comments: text });
        break;
      case 'observation':
        obj = await data.observation(parentId!, { owner: role, comments: text });
        break;
      case 'observation_detail': {
        parent = (await data.observation(parentId!, { owner: role })).id_observation;
        obj = await data.observationDetail(parent!);
        break;
      }
      case 'individual':
        obj = await data.individual({ owner: role, name: text });
        break;
      case 'marking':
        obj = await data.marking(parentId!, { owner: role, code: text });
        break;
    }
    const rowText = type === 'observation_detail' ? obj.uuid_observation_detail : text;
    entries.push({ owner, id: obj[OBJECTS[type].pk], listUrl: listUrl(type, parent), rowText });
  }
  return entries;
}

/** Prédicat de réponse API `<METHOD> /refacto/<module>/<endpoint>[/<id>]`. */
export const apiCall = (method: string, type: ObjectType, id?: number) => (r: Response) =>
  r.request().method() === method &&
  // la page détail d'un groupe de sites lit l'objet dans le contexte `generic`
  new RegExp(`/refacto/(${moduleOf(type)}|generic)/${OBJECTS[type].endpoint}${id ? `/${id}` : ''}(\\?.*)?$`).test(r.url());

/** Toute requête DELETE vers l'API du module (pour vérifier *quel* objet est supprimé). */
export const anyDelete = (r: Response) => r.request().method() === 'DELETE' && r.url().includes('/refacto/');

/** Onglet de liste affiché (les autres onglets peuvent rester dans le DOM). */
export const activeTabPanel = (page: Page) => page.locator('[role="tabpanel"]:visible');

export const propertiesForm = (page: Page) => page.locator('#properties-form');
export const validateButton = (page: Page) => propertiesForm(page).getByRole('button', { name: 'Valider', exact: true });

/**
 * Ouvre `url` dans un document neuf. Un `goto` qui ne change que le hash reste dans la même
 * application Angular : vers la même route (ex. `site/1` puis `site/2`), le composant est
 * réutilisé sans recharger l'objet, et une navigation précédente (retour au parent après une
 * suppression) peut encore être en cours.
 */
export async function gotoFresh(page: Page, url: string) {
  await page.goto('about:blank');
  await page.goto(url);
}

/** Réponse de la liste paginée d'un type (`GET /refacto/<module>/<endpoint>?...`). */
const listResponse = (type: ObjectType) => (r: Response) =>
  r.request().method() === 'GET' &&
  new RegExp(`/refacto/(${moduleOf(type)}|generic)/${OBJECTS[type].endpoint}\\?`).test(r.url());

/**
 * Ouvre l'onglet listant `type` sur la page `url` et renvoie ses lignes une fois la liste
 * chargée, ou `null` si l'onglet n'existe pas (liste masquée faute de droit de lecture).
 */
export async function openTab(page: Page, url: string, type: ObjectType): Promise<Locator | null> {
  const listed = page.waitForResponse(listResponse(type), { timeout: 10_000 }).catch(() => null);
  await gotoFresh(page, url);
  // page rendue (onglet « Propriétés » ou 1re liste), le chargement initial pouvant être long ;
  // puis un onglet de liste absent après un court délai correspond à une liste masquée
  await page.getByRole('tab').first().waitFor({ timeout: 30_000 });
  const tabLocator = page.getByRole('tab', { name: TYPES[type].tab });
  const shown = await tabLocator.waitFor({ timeout: 5_000 }).then(() => true, () => false);
  if (!shown) return null;
  await tabLocator.click();
  await listed;
  // rendu de la liste : des lignes ou le message « Pas de données disponibles »
  await activeTabPanel(page).locator('datatable-body-row, .empty-row').first().waitFor();
  return activeTabPanel(page).locator('datatable-body-row');
}

/**
 * Lignes d'une liste contenant `text`, ou `null` si l'onglet est absent. La liste étant paginée
 * côté serveur, si la ligne n'est pas sur la 1re page on filtre sur la colonne d'identification.
 */
export async function findRows(
  page: Page,
  url: string,
  type: ObjectType,
  text: string,
  displayList: string[],
) {
  const rows = await openTab(page, url, type);
  if (!rows) return null;
  const matching = rows.filter({ hasText: text });
  if ((await matching.count()) || (await rows.count()) < 10) return matching;
  const column = displayList.indexOf(TYPES[type].rowField);
  if (column < 0) return matching;
  const filtered = page.waitForResponse(listResponse(type));
  await activeTabPanel(page).locator('button:has(.fa-filter)').click();
  // 1re cellule d'en-tête = colonne « Action », sans filtre
  await activeTabPanel(page).locator('datatable-header-cell').nth(column + 1).locator('input').fill(text);
  await filtered;
  await activeTabPanel(page).locator('datatable-body-row, .empty-row').first().waitFor();
  return matching;
}

/** Ligne de liste contenant `text` (doit être visible). */
export async function listRow(
  page: Page,
  url: string,
  type: ObjectType,
  text: string,
  displayList: string[],
) {
  const rows = await findRows(page, url, type, text, displayList);
  expect(rows, `onglet ${TYPES[type].tab} absent`).not.toBeNull();
  const row = rows!.first();
  await expect(row).toBeVisible();
  return row;
}

/** Icône d'action d'une ligne de liste (`fa-trash`, `fa-plus`, `fa-edit`, `fa-eye`). */
export const rowAction = (row: Locator, icon: 'trash' | 'plus' | 'edit' | 'eye') => row.locator(`a.cell-link:has(.fa-${icon})`);

/** Bouton « Ajouter » de l'onglet courant. */
export const addButton = (page: Page) => activeTabPanel(page).getByRole('button', { name: /Ajouter/ });

export const confirmDeleteButton = (page: Page) => page.getByRole('button', { name: 'Confirmer la suppression' });

/** Collecte les requêtes d'écriture envoyées à l'API (pour vérifier qu'aucune n'est partie). */
export function recordWrites(page: Page) {
  const writes: string[] = [];
  page.on('request', (r) => {
    if (['POST', 'PATCH', 'DELETE'].includes(r.method()) && r.url().includes('/monitorings/')) {
      writes.push(`${r.method()} ${r.url()}`);
    }
  });
  return writes;
}
