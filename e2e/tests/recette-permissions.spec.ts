import { Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { Scope } from './permissions';
import { TestData, MODULE, MODULE_INDI, OBJECTS, ObjectType, moduleOf } from './data';
import { API, fillRequired, fillField, fieldByName } from './form-filler';
import { drawGeometry, uniqueName, MONITORING_URL } from './helpers';
import {
  SCOPES,
  OWNERS,
  TYPES,
  OBJECT_TYPES,
  Entry,
  allowed,
  detailUrl,
  moduleUrl,
  seedEntries,
  apiCall,
  anyDelete,
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
 * Recette des permissions du module Monitoring : pour chaque action (C, R, U, D, et E pour le
 * sous-module), chaque scope (0 aucun, 1 mes données, 2 mon organisme, 3 toutes) et chaque
 * contexte (Liste, Formulaire), on vérifie le comportement de l'UI sur chaque type d'objet.
 *
 * Pour R/U/D, chaque cas porte sur trois données : au compte testé, à un collègue du même
 * organisme, à un rôle d'un autre organisme ; le résultat attendu est donné par `allowed()`.
 * Pour C, seul compte « scope 0 » vs « scope > 0 ».
 *
 * Chaque test pose ses droits (un compte par worker, voir fixtures.ts) et crée ses données via
 * l'API avec le compte de préparation : les tests sont indépendants et parallélisables.
 * Pour R, un seul objet de permission varie (les pages parentes restent lisibles) ; pour C/U/D,
 * l'action varie sur tous les objets des sous-modules, R restant à 3.
 */

type Cfg = Record<string, Record<string, any>>;

/** Colonnes affichées en liste pour un type (config JSON du sous-module). */
const displayList = (cfg: Cfg, type: ObjectType): string[] => cfg[moduleOf(type)][type].display_list ?? [];

const ownersLabel = (scope: Scope, type: ObjectType) =>
  OWNERS.map((o) => `${o}:${allowed(type, scope, o) ? 'oui' : 'non'}`).join(' ');

/* ------------------------------------------------------------------------------------------ */
/* R – lecture                                                                                 */
/* ------------------------------------------------------------------------------------------ */

const PERM_OBJECTS_WITH_TYPES = [...new Set(OBJECT_TYPES.map((t) => TYPES[t].permObject))];

for (const permObject of PERM_OBJECTS_WITH_TYPES) {
  for (const scope of SCOPES) {
    test.describe(`R – ${permObject} – scope ${scope}`, () => {
      for (const type of OBJECT_TYPES.filter((t) => TYPES[t].permObject === permObject)) {
        const parent = TYPES[type].parent;
        // le parent partage l'objet de permission : au scope 0, sa page (et donc la liste) est refusée
        const parentHidden = scope === 0 && !!parent && TYPES[parent].permObject === permObject;

        test(`Liste – ${type} (${ownersLabel(scope, type)})`, async ({ page, grant, data, cfg }) => {
          // scope 0 : l'application ne demande pas la liste, `openTab` attend en vain sa réponse
          test.slow(scope === 0);
          await grant('R', scope, [permObject]);
          for (const entry of await seedEntries(data, type)) {
            if (parentHidden) {
              await gotoFresh(page, entry.listUrl);
              await page.waitForLoadState('networkidle');
              await expect(page.getByText(entry.rowText), 'ligne absente : page du parent refusée').toHaveCount(0);
              continue;
            }
            const rows = await findRows(page, entry.listUrl, type, entry.rowText, displayList(cfg, type));
            const visible = rows ? await rows.count() : 0;
            expect(visible > 0, `ligne de ${entry.owner} visible`).toBe(allowed(type, scope, entry.owner));
          }
        });

        test(`Formulaire – ${type} (${ownersLabel(scope, type)})`, async ({ page, grant, data }) => {
          await grant('R', scope, [permObject]);
          for (const entry of await seedEntries(data, type)) {
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
}

/* ------------------------------------------------------------------------------------------ */
/* C – création                                                                                */
/* ------------------------------------------------------------------------------------------ */

/** Remplit le formulaire de création d'un objet (champs requis issus de la config JSON). */
async function fillCreateForm(page: Page, cfg: Cfg, type: ObjectType) {
  const config = cfg[moduleOf(type)][type];
  switch (type) {
    case 'sites_group':
      await fillRequired(page, config, { sites_group_name: uniqueName('grp'), sites_group_code: 'E2E' });
      break;
    case 'site': {
      const typeSite = (await (await page.request.get(`${API}/monitorings/sites/types`)).json()).items[0].label;
      await fillRequired(page, config, { base_site_name: uniqueName('site'), types_site: typeSite });
      await drawGeometry(page, config.geometry_type);
      break;
    }
    case 'individual':
      await fillRequired(page, config, { individual_name: uniqueName('indi') });
      // `cd_nom` est requis par une expression JS : rempli explicitement
      await fillField(page, 'cd_nom', config.fields.cd_nom);
      break;
    default:
      await fillRequired(page, config);
  }
}

/** Valide le formulaire de création et vérifie le POST (objet suivi pour nettoyage). */
async function submitCreate(page: Page, data: TestData, type: ObjectType, button = validateButton(page)) {
  const post = page.waitForResponse(apiCall('POST', type));
  await expect(button).toBeEnabled();
  await button.click();
  const res = await post;
  expect(res.ok(), `POST ${type} : HTTP ${res.status()}`).toBe(true);
  const id = (await res.json())[OBJECTS[type].pk] as number;
  data.track(type, id);
  await expect(page.locator('.toast-message').first()).toContainText('Création');
  return id;
}

/** Parent (au compte testé) sous lequel créer un objet de `type` ; null = accueil du sous-module. */
async function seedParent(data: TestData, type: ObjectType): Promise<Entry | null> {
  const parent = TYPES[type].parent;
  return parent ? (await seedEntries(data, parent, ['me']))[0] : null;
}

for (const scope of SCOPES) {
  test.describe(`C – scope ${scope}`, () => {
    const label = scope > 0 ? 'autorisé' : 'interdit';

    for (const type of OBJECT_TYPES) {
      test(`Formulaire – ${type} (${label})`, async ({ page, grant, data, cfg }) => {
        await grant('C', scope);
        const parent = await seedParent(data, type);
        const url = parent ? detailUrl(TYPES[type].parent!, parent.id) : moduleUrl(moduleOf(type));
        expect(await openTab(page, url, type), `onglet ${TYPES[type].tab}`).not.toBeNull();
        const button = addButton(page);
        if (scope === 0) {
          await expect(button).toBeDisabled();
          return;
        }
        await button.click();
        await expect(propertiesForm(page)).toBeVisible();
        await fillCreateForm(page, cfg, type);
        await submitCreate(page, data, type);
      });

      const parentType = TYPES[type].parent;
      if (!parentType) continue; // pas de ligne parente : créé seulement via « Ajouter »
      test(`Liste – ${type} via « + » d’une ligne ${parentType} (${label})`, async ({
        page,
        grant,
        data,
        cfg,
        admin,
      }) => {
        await grant('C', scope);
        const parent = (await seedParent(data, type))!;
        const row = await listRow(page, parent.listUrl, parentType, parent.rowText, displayList(cfg, parentType));
        const plus = rowAction(row, 'plus');
        if (scope === 0) {
          await expect(plus).toHaveClass(/isDisableBtn/);
          await plus.dispatchEvent('click'); // sans défilement (ligne parfois hors zone défilable)
          await expect(propertiesForm(page)).toBeHidden();
          return;
        }
        await expect(plus).not.toHaveClass(/isDisableBtn/);
        await plus.click();
        await expect(page).toHaveURL(new RegExp(`${type}/create`));
        await fillCreateForm(page, cfg, type);
        const id = await submitCreate(page, data, type);
        const url = `${API}/monitorings/refacto/${moduleOf(type)}/${OBJECTS[type].endpoint}/${id}`;
        const created = await (await admin.get(url)).json();
        expect(created[OBJECTS[parentType].pk], 'rattaché à la ligne parente').toBe(parent.id);
      });
    }
  });
}

/* ------------------------------------------------------------------------------------------ */
/* U – modification                                                                            */
/* ------------------------------------------------------------------------------------------ */

/** Valide un formulaire d'édition : PATCH attendu si autorisé, sinon message et aucune écriture. */
async function submitEdit(page: Page, type: ObjectType, id: number, expected: boolean) {
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
  test.describe(`U – scope ${scope}`, () => {
    for (const type of OBJECT_TYPES) {
      test(`Liste – ${type} (${ownersLabel(scope, type)})`, async ({ page, grant, data, cfg }) => {
        await grant('U', scope);
        for (const entry of await seedEntries(data, type)) {
          const expected = allowed(type, scope, entry.owner);
          const row = await listRow(page, entry.listUrl, type, entry.rowText, displayList(cfg, type));
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

      test(`Formulaire – ${type} (${ownersLabel(scope, type)})`, async ({ page, grant, data }) => {
        await grant('U', scope);
        for (const entry of await seedEntries(data, type)) {
          await gotoFresh(page, detailUrl(type, entry.id));
          await page.getByRole('button', { name: 'Éditer' }).click();
          const expected = allowed(type, scope, entry.owner);
          await submitEdit(page, type, entry.id, expected);
        }
      });
    }
  });
}

/* ------------------------------------------------------------------------------------------ */
/* D – suppression                                                                             */
/* ------------------------------------------------------------------------------------------ */

/** Vérifie qu'un DELETE a visé le bon objet. */
async function expectDeleted(page: Page, type: ObjectType, id: number, deletePromise: Promise<any>) {
  const res = await deletePromise;
  expect(res.url(), 'la requête DELETE doit viser l’objet supprimé').toMatch(
    new RegExp(`/refacto/${moduleOf(type)}/${OBJECTS[type].endpoint}/${id}(\\?.*)?$`),
  );
  expect(res.status()).toBe(200);
  await expect(page.locator('.toast-message').first()).toContainText('Suppression');
}

for (const scope of SCOPES) {
  test.describe(`D – scope ${scope}`, () => {
    for (const type of OBJECT_TYPES) {
      test(`Liste – ${type} (${ownersLabel(scope, type)})`, async ({ page, grant, data, cfg }) => {
        await grant('D', scope);
        for (const entry of await seedEntries(data, type)) {
          const expected = allowed(type, scope, entry.owner);
          const row = await listRow(page, entry.listUrl, type, entry.rowText, displayList(cfg, type));
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

      test(`Formulaire – ${type} (${ownersLabel(scope, type)})`, async ({ page, grant, data }) => {
        await grant('D', scope);
        for (const entry of await seedEntries(data, type)) {
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

/* ------------------------------------------------------------------------------------------ */
/* Sous-module (MONITORINGS_MODULES) : R, U, E – sans propriétaire, seul scope 0 vs > 0 compte */
/* ------------------------------------------------------------------------------------------ */

for (const scope of SCOPES) {
  test.describe(`Module – scope ${scope}`, () => {
    const shown = scope > 0;

    test(`R – Liste – sous-module dans la liste des modules (${shown ? 'visible' : 'masqué'})`, async ({ page, grant }) => {
      await grant('R', scope, ['MONITORINGS_MODULES']);
      await page.goto(MONITORING_URL);
      // page des modules rendue (liste, ou message « pas de protocole accessible »)
      await expect(page.locator('h1.title-module')).toBeVisible();
      await page.waitForLoadState('networkidle');
      await expect(page.locator(`a[href*="/object/${MODULE}/sites_group"]`)).toHaveCount(shown ? 1 : 0);
    });

    test(`R – Formulaire – page du sous-module (${shown ? 'accessible' : 'refusée'})`, async ({ page, grant }) => {
      await grant('R', scope, ['MONITORINGS_MODULES']);
      await page.goto(moduleUrl(MODULE));
      if (!shown) {
        // redirection vers la liste des modules avec un message
        await expect(page.locator('.toast-message').first()).toContainText('permissions');
        await expect(page).not.toHaveURL(new RegExp(`object/${MODULE}`));
      }
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('button', { name: 'Éditer' })).toHaveCount(shown ? 1 : 0);
    });

    test(`U – Formulaire – édition du sous-module (${shown ? 'autorisée' : 'interdite'})`, async ({ page, grant }) => {
      await grant('U', scope, ['MONITORINGS_MODULES']);
      await page.goto(moduleUrl(MODULE));
      await page.getByRole('button', { name: 'Éditer' }).first().click();
      await expect(propertiesForm(page)).toBeVisible();
      await fieldByName(page, 'test').fill(uniqueName('module'));
      if (!shown) {
        const writes = recordWrites(page);
        await validateButton(page).click();
        await expect(page.locator('.toast-message').first()).toContainText('permissions');
        expect(writes).toEqual([]);
        return;
      }
      // pas de passage par la liste des modules (rendu de son composant ou `GET /monitorings/modules`)
      const modulesListLoads: string[] = [];
      page.on('request', (r) => {
        if (r.method() === 'GET' && /\/monitorings\/modules(\?|$)/.test(r.url())) modulesListLoads.push(r.url());
      });
      await page.evaluate(() => {
        new MutationObserver(() => {
          if (document.querySelector('pnx-monitoring-modules')) (window as any).__modulesListShown = true;
        }).observe(document.body, { childList: true, subtree: true });
      });
      const patch = page.waitForResponse((r) => r.request().method() === 'PATCH' && /\/module\/\d+$/.test(r.url()));
      await validateButton(page).click();
      expect((await patch).status()).toBe(200);
      await expect(page).toHaveURL(new RegExp(`object/${MODULE}/sites_group`));
      await expect(page.getByRole('button', { name: 'Éditer' }).first()).toBeVisible();
      const rendered = await page.evaluate(() => !!(window as any).__modulesListShown);
      expect({ rendered, loaded: modulesListLoads.length > 0 }, 'passage par la liste des modules').toEqual({
        rendered: false,
        loaded: false,
      });
    });

    test(`E – Formulaire – bouton Téléchargements (${shown ? 'visible' : 'masqué'})`, async ({ page, grant }) => {
      await grant('E', scope, ['MONITORINGS_MODULES']);
      await page.goto(moduleUrl(MODULE));
      await expect(page.getByRole('button', { name: 'Éditer' }).first()).toBeVisible();
      await expect(page.getByRole('button', { name: /Téléchargements/ })).toHaveCount(shown ? 1 : 0);
    });
  });
}

/* ------------------------------------------------------------------------------------------ */
/* Saisie enchaînée (indépendante des scopes)                                                  */
/* ------------------------------------------------------------------------------------------ */

test('Formulaire – Create chain – individus : saisies enchaînées', async ({ page, grant, data, cfg }) => {
  await grant();
  expect(await openTab(page, moduleUrl(MODULE_INDI), 'individual')).not.toBeNull();
  await addButton(page).click();
  await page.locator('#toggle-btn mat-slide-toggle button, #toggle-btn mat-slide-toggle input').first().click();
  const chainButton = page.getByRole('button', { name: 'Valider et enchainer les saisies' });

  await fillCreateForm(page, cfg, 'individual');
  await submitCreate(page, data, 'individual', chainButton);
  // le formulaire est réinitialisé sur place pour la saisie suivante
  await expect(page).toHaveURL(/individual\/create/);
  await expect(fieldByName(page, 'individual_name')).toHaveValue('');

  await fillCreateForm(page, cfg, 'individual');
  await submitCreate(page, data, 'individual', chainButton);
  await expect(page).toHaveURL(/individual\/create/);
});
