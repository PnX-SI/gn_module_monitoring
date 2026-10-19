import { APIRequestContext, request as pwRequest, expect } from '@playwright/test';
import { API } from './form-filler';

/**
 * Pilotage des permissions CRUVED via l'admin Flask de GeoNature
 * (`/admin/permissions/permission/`), GeoNature n'exposant pas d'API REST d'écriture des
 * permissions. Nécessite un compte ayant les droits ADMIN > PERMISSIONS (ex. membre de Grp_admin).
 *
 * Modèle : une permission = (rôle, availability, scope) où availability vaut
 * `<id_module>:<id_object>:<id_action>` et scope `__None` (toutes les données = 3), `1` ou `2`.
 * Un scope 0 se traduit par l'absence de permission.
 */

export const ADMIN_USER = process.env.GN_ADMIN_USER ?? 'admin';
export const ADMIN_PASSWORD = process.env.GN_ADMIN_PASSWORD ?? 'admin';
const PERM_ADMIN = `${API}/admin/permissions/permission`;

export type Action = 'C' | 'R' | 'U' | 'V' | 'E' | 'D';
export type Scope = 0 | 1 | 2 | 3;
/** `{ <code_object>: { <action>: <scope> } }`, ex. `{ MONITORINGS_GRP_SITES: { R: 3, D: 0 } }` */
export type PermissionSpec = Record<string, Partial<Record<Action, Scope>>>;

/** Contexte HTTP authentifié (cookie `token`) pour un utilisateur GeoNature. */
export async function loginContext(login: string, password: string): Promise<APIRequestContext> {
  // état vierge : ne pas hériter du storageState du projet
  const ctx = await pwRequest.newContext({ storageState: { cookies: [], origins: [] } });
  const res = await ctx.post(`${API}/auth/login`, { data: { login, password } });
  if (!res.ok()) throw new Error(`login ${login}: HTTP ${res.status()}`);
  return ctx;
}

export const adminContext = () => loginContext(ADMIN_USER, ADMIN_PASSWORD);

/** id_role de l'utilisateur connecté sur le contexte. */
export async function currentRoleId(ctx: APIRequestContext): Promise<number> {
  const res = await ctx.get(`${API}/auth/get_current_user`);
  if (!res.ok()) throw new Error(`get_current_user: HTTP ${res.status()}`);
  return (await res.json()).user.id_role;
}

const availabilityCache = new Map<string, string>();

/**
 * Valeur `<id_module>:<id_object>:<id_action>` d'une permission disponible : on laisse
 * l'admin la pré-sélectionner (`create_form` lit module_code/code_object/code_action).
 */
async function availability(admin: APIRequestContext, moduleCode: string, object: string, action: Action) {
  const key = `${moduleCode}:${object}:${action}`;
  if (!availabilityCache.has(key)) {
    const params = new URLSearchParams({ module_code: moduleCode, code_object: object, code_action: action });
    const html = await (await admin.get(`${PERM_ADMIN}/new/?${params}`)).text();
    const m = html.match(/<option[^>]*\bselected\b[^>]*value="(\d+:\d+:\d+)"/);
    if (!m) throw new Error(`Aucune permission disponible pour ${key}`);
    availabilityCache.set(key, m[1]);
  }
  return availabilityCache.get(key)!;
}

/** Ids des permissions d'un rôle sur un module (liste filtrée de l'admin). */
async function listPermissionIds(admin: APIRequestContext, idRole: number, idModule: number) {
  const params = new URLSearchParams({
    flt0_rle_equals: String(idRole),
    flt1_module_equals: String(idModule),
    page_size: '500',
  });
  const html = await (await admin.get(`${PERM_ADMIN}/?${params}`)).text();
  return [...html.matchAll(/name="rowid"[^>]*value="(\d+)"/g)].map((m) => Number(m[1]));
}

async function deletePermission(admin: APIRequestContext, id: number) {
  const res = await admin.post(`${PERM_ADMIN}/delete/`, {
    form: { id: String(id), url: `${PERM_ADMIN}/` },
    maxRedirects: 0,
  });
  if (res.status() !== 302) throw new Error(`suppression permission ${id}: HTTP ${res.status()}`);
}

/** Crée une permission et renvoie son id (« Save and Continue Editing » redirige vers edit/?id=). */
async function addPermission(admin: APIRequestContext, idRole: number, availabilityValue: string, scope: Scope) {
  const res = await admin.post(`${PERM_ADMIN}/new/`, {
    form: {
      role: String(idRole),
      availability: availabilityValue,
      scope: scope === 3 ? '__None' : String(scope),
      expire_on: '',
      _continue_editing: 'Save and Continue Editing',
    },
    maxRedirects: 0,
  });
  const id = res.headers()['location']?.match(/[?&]id=(\d+)/)?.[1];
  // un ré-affichage du formulaire (200) signale une erreur de validation
  if (res.status() !== 302 || !id) throw new Error(`ajout permission ${availabilityValue}: HTTP ${res.status()}`);
  return Number(id);
}

/**
 * Permissions directes d'un rôle, appliquées par différence : seul ce qui change entre deux
 * `apply` est écrit. Au premier `apply` d'un module, les permissions existantes du rôle sur ce
 * module sont supprimées, pour partir d'un état connu.
 */
export class PermissionManager {
  /** module → `objet:action` → permission posée */
  private state = new Map<string, Map<string, { scope: Scope; id: number }>>();

  constructor(
    private admin: APIRequestContext,
    readonly idRole: number,
  ) {}

  async apply(moduleCode: string, spec: PermissionSpec) {
    let current = this.state.get(moduleCode);
    if (!current) {
      current = new Map();
      const [object, actions] = Object.entries(spec)[0];
      const anyAvailability = await availability(this.admin, moduleCode, object, Object.keys(actions)[0] as Action);
      const idModule = Number(anyAvailability.split(':')[0]);
      for (const id of await listPermissionIds(this.admin, this.idRole, idModule)) {
        await deletePermission(this.admin, id);
      }
      this.state.set(moduleCode, current);
    }
    const wanted = new Map<string, Scope>();
    for (const [object, actions] of Object.entries(spec)) {
      for (const [action, scope] of Object.entries(actions) as [Action, Scope][]) {
        wanted.set(`${object}:${action}`, scope);
      }
    }
    for (const key of new Set([...wanted.keys(), ...current.keys()])) {
      const scope = wanted.get(key) ?? 0;
      const existing = current.get(key);
      if ((existing?.scope ?? 0) === scope) continue;
      if (existing) {
        await deletePermission(this.admin, existing.id);
        current.delete(key);
      }
      if (scope > 0) {
        const [object, action] = key.split(':') as [string, Action];
        const value = await availability(this.admin, moduleCode, object, action);
        current.set(key, { scope, id: await addPermission(this.admin, this.idRole, value, scope) });
      }
    }
  }
}

/** Remplace toutes les permissions directes du rôle sur le module par `spec`. */
export async function setPermissions(admin: APIRequestContext, idRole: number, moduleCode: string, spec: PermissionSpec) {
  await new PermissionManager(admin, idRole).apply(moduleCode, spec);
}

/** Même CRUD (+ export module) au scope donné sur tous les objets de permission listés. */
export function fullCrud(objects: string[], scope: Scope = 3): PermissionSpec {
  const spec: PermissionSpec = {};
  for (const o of objects) {
    spec[o] = o === 'MONITORINGS_MODULES' ? { R: scope, U: scope, E: scope } : { C: scope, R: scope, U: scope, D: scope };
  }
  return spec;
}

/**
 * Vérifie que les droits effectifs de l'utilisateur (permissions propres + groupes) sont bien
 * ceux posés : un groupe qui accorderait davantage fausserait les tests de restriction.
 */
export async function expectEffectiveCruved(
  user: APIRequestContext,
  moduleCode: string,
  object: string,
  expected: Partial<Record<Action, Scope>>,
) {
  const modules: any[] = await (await user.get(`${API}/gn_commons/modules`)).json();
  const module = modules.find((m) => m.module_code === moduleCode);
  const cruved = module?.objects?.find((o: any) => o.code_object === object)?.cruved ?? module?.cruved ?? {};
  for (const [action, scope] of Object.entries(expected)) {
    expect(
      cruved[action] ?? 0,
      `${moduleCode}/${object}/${action} : droit effectif différent du droit posé (hérité d'un groupe ?)`,
    ).toBe(scope);
  }
}
