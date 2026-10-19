import { test as base, APIRequestContext } from '@playwright/test';
import fs from 'node:fs';
import { adminContext, loginContext, currentRoleId, PermissionManager, Action, Scope } from './permissions';
import { TestData, MODULE, MODULE_INDI, ensureUserDataset } from './data';
import { getModuleConfig } from './form-filler';
import { permissionsFor, monitoringsSpec } from './recette';

/**
 * Un compte de test par worker Playwright (`e2e.worker<n>`, créés par
 * `scripts/create_test_users.py`) : chaque worker fait varier ses propres permissions, ce qui
 * permet d'exécuter la recette en parallèle.
 */
export const USER_PREFIX = process.env.GN_USER_PREFIX ?? 'e2e.worker';
export const USER_PASSWORD = process.env.GN_USER_PASSWORD ?? 'e2e-password';
export const WORKERS = Number(process.env.GN_WORKERS ?? 4);

export const accountLogin = (parallelIndex: number) => `${USER_PREFIX}${parallelIndex + 1}`;

export type Account = { login: string; idRole: number; idDataset: number };

/** Hôtes des fonds de carte : inutiles aux tests, bloqués pour accélérer les pages. */
const MAP_TILES = /tile\.openstreetmap\.org|wxs\.ign\.fr|data\.geopf\.fr|arcgisonline\.com|tile\./;

type WorkerFixtures = {
  account: Account;
  /** compte aux droits complets qui prépare les données et pose les permissions */
  admin: APIRequestContext;
  /** API avec le compte testé */
  user: APIRequestContext;
  perms: PermissionManager;
  /** config JSON fusionnée des sous-modules de test */
  cfg: Record<string, Record<string, any>>;
  workerStorageState: string;
};

type TestFixtures = {
  /** données du test, supprimées à la fin du test */
  data: TestData;
  /** droits du compte testé : tout à 3, sauf `action` = `scope` sur `objects` (tous si absent) */
  grant: (action?: Action, scope?: Scope, objects?: string[]) => Promise<void>;
  /** droits du compte testé dans le gestionnaire de sites (MONITORINGS) : tout à 3, sauf `action` = `scope` */
  grantGeneric: (action?: Action, scope?: Scope, objects?: string[]) => Promise<void>;
};

export const test = base.extend<TestFixtures, WorkerFixtures>({
  account: [
    async ({}, use, workerInfo) => {
      const login = accountLogin(workerInfo.parallelIndex);
      const user = await loginContext(login, USER_PASSWORD);
      const idRole = await currentRoleId(user);
      const admin = await adminContext();
      await use({ login, idRole, idDataset: await ensureUserDataset(admin, login, idRole) });
      await user.dispose();
      await admin.dispose();
    },
    { scope: 'worker' },
  ],

  admin: [
    async ({}, use) => {
      const admin = await adminContext();
      await use(admin);
      await admin.dispose();
    },
    { scope: 'worker' },
  ],

  user: [
    async ({ account }, use) => {
      const user = await loginContext(account.login, USER_PASSWORD);
      await use(user);
      await user.dispose();
    },
    { scope: 'worker' },
  ],

  perms: [async ({ admin, account }, use) => use(new PermissionManager(admin, account.idRole)), { scope: 'worker' }],

  cfg: [
    async ({ admin }, use) => {
      await use({ [MODULE]: await getModuleConfig(admin, MODULE), [MODULE_INDI]: await getModuleConfig(admin, MODULE_INDI) });
    },
    { scope: 'worker' },
  ],

  // session navigateur du compte du worker
  workerStorageState: [
    async ({ browser, account }, use, workerInfo) => {
      const file = `.auth/worker-${workerInfo.parallelIndex}.json`;
      fs.mkdirSync('.auth', { recursive: true });
      const page = await browser.newPage({ storageState: undefined, baseURL: workerInfo.project.use.baseURL });
      await page.goto('/#/login');
      await page.getByRole('textbox', { name: "Nom d'utilisateur" }).fill(account.login);
      await page.getByRole('textbox', { name: 'Mot de passe' }).fill(USER_PASSWORD);
      await page.getByRole('button', { name: 'Se connecter' }).click();
      await page.waitForURL((url) => !url.hash.includes('login'));
      await page.context().storageState({ path: file });
      await page.close();
      await use(file);
    },
    { scope: 'worker' },
  ],

  storageState: ({ workerStorageState }, use) => use(workerStorageState),

  page: async ({ page }, use) => {
    await page.route(MAP_TILES, (route) => route.abort());
    await use(page);
  },

  data: async ({ admin, account }, use) => {
    const data = new TestData(admin, account);
    await use(data);
    await data.cleanup();
  },

  grant: async ({ perms }, use) => {
    await use(async (action, scope, objects) => {
      for (const module of [MODULE, MODULE_INDI]) {
        await perms.apply(module, permissionsFor(module, action, scope, objects));
      }
      // droits MONITORINGS éventuellement modifiés par un test du gestionnaire de sites
      await perms.apply('MONITORINGS', monitoringsSpec());
    });
  },

  grantGeneric: async ({ perms }, use) => {
    await use(async (action, scope, objects) => {
      for (const module of [MODULE, MODULE_INDI]) {
        await perms.apply(module, permissionsFor(module));
      }
      await perms.apply('MONITORINGS', monitoringsSpec(action, scope, objects));
    });
  },
});

export { expect } from '@playwright/test';
