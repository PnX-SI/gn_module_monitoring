import { Page, Response } from '@playwright/test';
import { test, expect } from './fixtures';
import { Scope } from './permissions';
import { TestData, OBJECTS } from './data';
import { API, fillRequired, getModuleConfig, fieldByName } from './form-filler';
import { drawGeometry, uniqueName, selectNgOption, MONITORING_URL } from './helpers';
import {
  SCOPES,
  OWNERS,
  TYPES,
  Entry,
  allowed,
  seedEntries,
  propertiesForm,
  validateButton,
  openTab,
  findRows,
  listRow,
  rowAction,
  addButton,
  confirmDeleteButton,
  recordWrites,
  gotoFresh,
} from './recette';

/**
 * Recette des permissions du gestionnaire de sites (contexte `generic` : groupes de sites et
 * sites de tous les sous-modules). Les droits sont ceux du module MONITORINGS, objets
 * MONITORINGS_GRP_SITES et MONITORINGS_SITES ; mêmes règles de scope que dans les sous-modules.
 *
 * Les données sont créées via l'API d'un sous-module de test (elles apparaissent aussi dans le
 * gestionnaire de sites) ; l'UI est pilotée dans le contexte `generic`.
 */

type GenericType = 'sites_group' | 'site';
const GENERIC_TYPES: GenericType[] = ['sites_group', 'site'];
const GENERIC = 'generic';

const homeUrl = `${MONITORING_URL}/object/${GENERIC}/sites_group`;
/** Page détail dans le gestionnaire de sites, avec les `parents_path` posés par sa navigation. */
const detailUrl = (type: GenericType, id: number) =>
  `${MONITORING_URL}/object/${GENERIC}/${type}/${id}?parents_path=module${type === 'site' ? '&parents_path=sites_group' : ''}`;

/** Les groupes de sites sont listés sur l'accueil, les sites sur la page de leur groupe. */
async function genericEntries(data: TestData, type: GenericType, owners = OWNERS): Promise<Entry[]> {
  const entries = await seedEntries(data, type, owners);
  if (type === 'sites_group') return entries.map((e) => ({ ...e, listUrl: homeUrl }));
  const idSitesGroup = Number(entries[0].listUrl.match(/sites_group\/(\d+)/)![1]);
  return entries.map((e) => ({ ...e, listUrl: detailUrl('sites_group', idSitesGroup) }));
}

/** Prédicat de réponse API du contexte `generic`. */
const apiCall = (method: string, type: GenericType, id?: number) => (r: Response) =>
  r.request().method() === method &&
  new RegExp(`/refacto/${GENERIC}/${OBJECTS[type].endpoint}${id ? `/${id}` : ''}(\\?.*)?$`).test(r.url());

const anyDelete = (r: Response) => r.request().method() === 'DELETE' && r.url().includes('/refacto/');

const ownersLabel = (scope: Scope, type: GenericType) =>
  OWNERS.map((o) => `${o}:${allowed(type, scope, o) ? 'oui' : 'non'}`).join(' ');

// l'accueil du gestionnaire de sites (tous les groupes de sites et leurs géométries) est long à
// charger, et un test de liste l'ouvre une fois par propriétaire
test.describe.configure({ timeout: 90_000 });

let genericCfg: Record<string, any>;
test.beforeAll(async ({ admin }) => {
  genericCfg = await getModuleConfig(admin, GENERIC);
});
const displayList = (type: GenericType): string[] => genericCfg[type].display_list ?? [];

/* ------------------------------------------------------------------------------------------ */
/* Accès                                                                                       */
/* ------------------------------------------------------------------------------------------ */

for (const scope of SCOPES) {
  const shown = scope > 0;
  test(`Accès – scope ${scope} – bouton « Gestionnaire de sites » (${shown ? 'actif' : 'inactif'})`, async ({
    page,
    grantGeneric,
  }) => {
    await grantGeneric('R', scope);
    await page.goto(MONITORING_URL);
    await expect(page.locator('h1.title-module')).toBeVisible();
    const button = page.locator('button', { has: page.locator('mat-icon', { hasText: /^\s*map\s*$/ }) });
    if (shown) await expect(button).toBeEnabled();
    else await expect(button).toBeDisabled();
  });
}

/* ------------------------------------------------------------------------------------------ */
/* R – lecture                                                                                 */
/* ------------------------------------------------------------------------------------------ */

for (const scope of SCOPES) {
  test.describe(`Gestionnaire de sites – R – scope ${scope}`, () => {
    for (const type of GENERIC_TYPES) {
      test(`Liste – ${type} (${ownersLabel(scope, type)})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('R', scope, [TYPES[type].permObject]);
        for (const entry of await genericEntries(data, type)) {
          const rows = await findRows(page, entry.listUrl, type, entry.rowText, displayList(type));
          const visible = rows ? await rows.count() : 0;
          expect(visible > 0, `ligne de ${entry.owner} visible`).toBe(allowed(type, scope, entry.owner));
        }
      });

      test(`Formulaire – ${type} (${ownersLabel(scope, type)})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('R', scope, [TYPES[type].permObject]);
        for (const entry of await genericEntries(data, type)) {
          const get = page.waitForResponse(apiCall('GET', type, entry.id));
          await gotoFresh(page, detailUrl(type, entry.id));
          const expected = allowed(type, scope, entry.owner);
          expect((await get).status(), `GET ${type} de ${entry.owner}`).toBe(expected ? 200 : 403);
          if (expected) await expect(page.locator('td.td-value').first()).toBeVisible();
        }
      });
    }
  });
}

/* ------------------------------------------------------------------------------------------ */
/* C – création                                                                                */
/* ------------------------------------------------------------------------------------------ */

async function fillCreateForm(page: Page, type: GenericType) {
  const config = genericCfg[type];
  if (type === 'sites_group') {
    await fillRequired(page, config, { sites_group_name: uniqueName('grp'), sites_group_code: 'E2E' });
    // liste des modules chargée de façon asynchrone : un choix trop tôt peut rester vide
    const modules = fieldByName(page, 'modules');
    await expect(async () => {
      if (await modules.locator('.ng-value').count()) return;
      await selectNgOption(page, modules.locator('input').first());
      expect(await modules.locator('.ng-value').count()).toBeGreaterThan(0);
    }).toPass({ timeout: 15_000 });
    return;
  }
  const typeSite = (await (await page.request.get(`${API}/monitorings/sites/types`)).json()).items[0].label;
  await fillRequired(page, config, { base_site_name: uniqueName('site'), types_site: typeSite });
  await drawGeometry(page, config.geometry_type);
}

async function submitCreate(page: Page, data: TestData, type: GenericType) {
  const post = page.waitForResponse(apiCall('POST', type));
  await expect(validateButton(page)).toBeEnabled();
  await validateButton(page).click();
  const res = await post;
  expect(res.ok(), `POST ${type} : HTTP ${res.status()}`).toBe(true);
  const id = (await res.json())[OBJECTS[type].pk] as number;
  data.track(type, id);
  await expect(page.locator('.toast-message').first()).toContainText('Création');
  return id;
}

for (const scope of SCOPES) {
  test.describe(`Gestionnaire de sites – C – scope ${scope}`, () => {
    const label = scope > 0 ? 'autorisé' : 'interdit';

    for (const type of GENERIC_TYPES) {
      test(`Formulaire – ${type} depuis l’accueil (${label})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('C', scope);
        expect(await openTab(page, homeUrl, type), `onglet ${TYPES[type].tab}`).not.toBeNull();
        const button = addButton(page);
        if (scope === 0) {
          await expect(button).toBeDisabled();
          return;
        }
        await button.click();
        await expect(propertiesForm(page)).toBeVisible();
        await fillCreateForm(page, type);
        await submitCreate(page, data, type);
      });
    }

    test(`Liste – site via « + » d’une ligne sites_group (${label})`, async ({ page, grantGeneric, data, admin }) => {
      await grantGeneric('C', scope);
      const [parent] = await genericEntries(data, 'sites_group', ['me']);
      const row = await listRow(page, parent.listUrl, 'sites_group', parent.rowText, displayList('sites_group'));
      const plus = rowAction(row, 'plus');
      if (scope === 0) {
        await expect(plus).toHaveClass(/isDisableBtn/);
        await plus.dispatchEvent('click'); // sans défilement (ligne parfois hors zone défilable)
        await expect(propertiesForm(page)).toBeHidden();
        return;
      }
      await expect(plus).not.toHaveClass(/isDisableBtn/);
      await plus.click();
      await expect(page).toHaveURL(/site\/create/);
      await fillCreateForm(page, 'site');
      const id = await submitCreate(page, data, 'site');
      const created = await (await admin.get(`${API}/monitorings/refacto/${GENERIC}/sites/${id}`)).json();
      expect(created.id_sites_group, 'rattaché à la ligne parente').toBe(parent.id);
    });
  });
}

/* ------------------------------------------------------------------------------------------ */
/* U – modification                                                                            */
/* ------------------------------------------------------------------------------------------ */

async function submitEdit(page: Page, type: GenericType, id: number, expected: boolean) {
  await expect(propertiesForm(page)).toBeVisible();
  if (expected) {
    const patch = page.waitForResponse(apiCall('PATCH', type, id));
    await validateButton(page).click();
    // la route PATCH des sites répond 201
    expect((await patch).ok(), `PATCH ${type}`).toBe(true);
    await expect(page.locator('.toast-message').first()).toContainText('Modification');
  } else {
    const writes = recordWrites(page);
    await validateButton(page).click();
    await expect(page.locator('.toast-message').first()).toContainText('permissions');
    expect(writes).toEqual([]);
  }
}

for (const scope of SCOPES) {
  test.describe(`Gestionnaire de sites – U – scope ${scope}`, () => {
    for (const type of GENERIC_TYPES) {
      test(`Liste – ${type} (${ownersLabel(scope, type)})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('U', scope);
        for (const entry of await genericEntries(data, type)) {
          const expected = allowed(type, scope, entry.owner);
          const row = await listRow(page, entry.listUrl, type, entry.rowText, displayList(type));
          const edit = rowAction(row, 'edit');
          if (!expected) {
            await expect(edit, `édition de la ligne de ${entry.owner}`).toHaveClass(/isDisableBtn/);
            await edit.dispatchEvent('click'); // sans défilement (ligne parfois hors zone défilable)
            await expect(propertiesForm(page)).toBeHidden();
            continue;
          }
          await expect(edit, `édition de la ligne de ${entry.owner}`).not.toHaveClass(/isDisableBtn/);
          await edit.click();
          await submitEdit(page, type, entry.id, true);
        }
      });

      test(`Formulaire – ${type} (${ownersLabel(scope, type)})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('U', scope);
        for (const entry of await genericEntries(data, type)) {
          await gotoFresh(page, detailUrl(type, entry.id));
          await page.getByRole('button', { name: 'Éditer' }).click();
          await submitEdit(page, type, entry.id, allowed(type, scope, entry.owner));
        }
      });
    }
  });
}

/* ------------------------------------------------------------------------------------------ */
/* D – suppression                                                                             */
/* ------------------------------------------------------------------------------------------ */

async function expectDeleted(page: Page, type: GenericType, id: number, deletePromise: Promise<Response>) {
  const res = await deletePromise;
  expect(res.url(), 'la requête DELETE doit viser l’objet supprimé').toMatch(
    new RegExp(`/refacto/${GENERIC}/${OBJECTS[type].endpoint}/${id}(\\?.*)?$`),
  );
  expect(res.status()).toBe(200);
  await expect(page.locator('.toast-message').first()).toContainText('Suppression');
}

for (const scope of SCOPES) {
  test.describe(`Gestionnaire de sites – D – scope ${scope}`, () => {
    for (const type of GENERIC_TYPES) {
      test(`Liste – ${type} (${ownersLabel(scope, type)})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('D', scope);
        for (const entry of await genericEntries(data, type)) {
          const expected = allowed(type, scope, entry.owner);
          const row = await listRow(page, entry.listUrl, type, entry.rowText, displayList(type));
          const trash = rowAction(row, 'trash');
          if (!expected) {
            await expect(trash, `suppression de la ligne de ${entry.owner}`).toHaveClass(/isDisableBtn/);
            const writes = recordWrites(page);
            await trash.dispatchEvent('click'); // sans défilement (ligne parfois hors zone défilable)
            await expect(confirmDeleteButton(page)).toBeHidden();
            expect(writes).toEqual([]);
            continue;
          }
          await expect(trash, `suppression de la ligne de ${entry.owner}`).not.toHaveClass(/isDisableBtn/);
          const del = page.waitForResponse(anyDelete);
          await trash.click();
          await confirmDeleteButton(page).click();
          await expectDeleted(page, type, entry.id, del);
        }
      });

      test(`Formulaire – ${type} (${ownersLabel(scope, type)})`, async ({ page, grantGeneric, data }) => {
        await grantGeneric('D', scope);
        for (const entry of await genericEntries(data, type)) {
          const expected = allowed(type, scope, entry.owner);
          await gotoFresh(page, detailUrl(type, entry.id));
          await page.getByRole('button', { name: 'Éditer' }).click();
          const remove = propertiesForm(page).getByRole('button', { name: 'Supprimer', exact: true });
          if (!expected) {
            await expect(remove, `suppression de l’objet de ${entry.owner}`).toBeDisabled();
            continue;
          }
          await expect(remove, `suppression de l’objet de ${entry.owner}`).toBeEnabled();
          const del = page.waitForResponse(anyDelete);
          await remove.click();
          await confirmDeleteButton(page).click();
          await expectDeleted(page, type, entry.id, del);
        }
      });
    }
  });
}
