import { test as setup } from '@playwright/test';
import { adminContext, loginContext, currentRoleId, setPermissions } from './permissions';
import { MODULE, MODULE_INDI, ensureModuleConfigured, ensureUserDataset } from './data';
import { permissionsFor, monitoringsSpec } from './recette';
import { WORKERS, USER_PASSWORD, accountLogin } from './fixtures';

/**
 * Prépare l'instance : sous-modules de test configurés (sinon le front bloque l'accès, #752),
 * droits complets du compte de préparation (admin), et pour chaque compte de worker ses droits
 * MONITORINGS et son jeu de données.
 */
setup('sous-modules et comptes de test', async () => {
  setup.setTimeout(180_000);
  const admin = await adminContext();
  const idAdmin = await currentRoleId(admin);
  for (const module of [MODULE, MODULE_INDI]) {
    await setPermissions(admin, idAdmin, module, permissionsFor(module));
    await ensureModuleConfigured(admin, module);
  }
  for (let i = 0; i < WORKERS; i++) {
    const login = accountLogin(i);
    const user = await loginContext(login, USER_PASSWORD).catch(() => {
      throw new Error(`Compte ${login} absent : lancer scripts/create_test_users.py --count ${WORKERS}`);
    });
    const idRole = await currentRoleId(user);
    await setPermissions(admin, idRole, 'MONITORINGS', monitoringsSpec());
    await ensureUserDataset(admin, login, idRole);
    await user.dispose();
  }
});
