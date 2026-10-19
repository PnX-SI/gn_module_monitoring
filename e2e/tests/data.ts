import { APIRequestContext } from '@playwright/test';
import { API } from './form-filler';
import { uniqueName } from './helpers';

/**
 * Création / suppression de données de test via l'API du module (`/monitorings/refacto/...`),
 * pour préparer les objets testés par l'UI et nettoyer ensuite.
 */

const REFACTO = `${API}/monitorings/refacto`;

/** Sous-modules de test installés depuis `contrib/` (voir README). */
export const MODULE = process.env.GN_MODULE ?? 'e2e_test'; // groupe de sites > site > visite > observation > détail
export const MODULE_INDI = process.env.GN_MODULE_INDI ?? 'e2e_test_indi'; // individu > marquage

/** Segment d'URL API et clé primaire par type d'objet. */
export const OBJECTS = {
  sites_group: { endpoint: 'sites_groups', pk: 'id_sites_group' },
  site: { endpoint: 'sites', pk: 'id_base_site' },
  visit: { endpoint: 'visits', pk: 'id_base_visit' },
  observation: { endpoint: 'observations', pk: 'id_observation' },
  observation_detail: { endpoint: 'observation_details', pk: 'id_observation_detail' },
  individual: { endpoint: 'individuals', pk: 'id_individual' },
  marking: { endpoint: 'markings', pk: 'id_marking' },
} as const;
export type ObjectType = keyof typeof OBJECTS;

export const moduleOf = (type: ObjectType) => (['individual', 'marking'].includes(type) ? MODULE_INDI : MODULE);

type Created = { type: ObjectType; id: number };
type Refs = { idRole: number; idModule: number; idDataset: number; idTypeSite: number; cdNom: number; idMarkingType: number };

/**
 * Fabrique de données, utilisée avec un compte aux droits complets (admin) pour préparer les
 * données d'un test quels que soient les droits de l'utilisateur testé. Garde la trace de ce
 * qu'elle crée pour `cleanup()` (ordre inverse, erreurs ignorées : l'objet a pu être supprimé).
 *
 * `owner` (id_role) renseigne les champs qui déterminent l'appartenance de la donnée pour les
 * scopes 1/2 (numérisateur, observateurs, inventeur, opérateur) ; par défaut `me`, l'utilisateur
 * testé. Les visites sont rattachées au jeu de données de l'utilisateur testé (`idDataset`).
 */
export class TestData {
  private created: Created[] = [];
  private refs: Promise<Refs> | undefined;

  constructor(
    private api: APIRequestContext,
    private me: { idRole: number; idDataset: number },
  ) {}

  /** Références nécessaires aux payloads, lues dans la config (`custom`) du module principal. */
  references() {
    this.refs ??= (async () => {
      const custom = (await (await this.api.get(`${REFACTO}/${MODULE}/config`)).json()).custom;
      const idList = custom['__MODULE.ID_LIST_TAXONOMY'];
      const taxa = await (await this.api.get(`${API}/taxhub/api/taxref/allnamebylist/${idList}?limit=1`)).json();
      const markingTypes = await (await this.api.get(`${API}/nomenclatures/nomenclature/TYP_MARQUAGE`)).json();
      return {
        idRole: this.me.idRole,
        idModule: custom['__MODULE.ID_MODULE'],
        idDataset: this.me.idDataset,
        idTypeSite: custom['__MODULE.IDS_TYPE_SITE'][0].id_nomenclature_type_site,
        cdNom: taxa[0].cd_nom,
        idMarkingType: markingTypes.values[0].id_nomenclature,
      };
    })();
    return this.refs;
  }

  /** POST et renvoie l'objet créé (JSON de l'API). */
  async create(type: ObjectType, payload: Record<string, unknown>): Promise<Record<string, any>> {
    const { endpoint, pk } = OBJECTS[type];
    const res = await this.api.post(`${REFACTO}/${moduleOf(type)}/${endpoint}`, { data: payload });
    if (!res.ok()) throw new Error(`POST ${type}: HTTP ${res.status()} ${await res.text()}`);
    const obj = await res.json();
    this.created.push({ type, id: obj[pk] });
    return obj;
  }

  /** L'objet existe-t-il encore ? (lu avec les droits complets du compte de préparation) */
  async exists(type: ObjectType, id: number) {
    const res = await this.api.get(`${REFACTO}/${moduleOf(type)}/${OBJECTS[type].endpoint}/${id}`);
    return res.ok();
  }

  /** Enregistre un objet créé par l'UI pour qu'il soit nettoyé. */
  track(type: ObjectType, id: number) {
    this.created.push({ type, id });
  }

  async cleanup() {
    for (const { type, id } of this.created.reverse()) {
      await this.api.delete(`${REFACTO}/${moduleOf(type)}/${OBJECTS[type].endpoint}/${id}`).catch(() => undefined);
    }
    this.created = [];
  }

  private async owner(owner?: number) {
    return owner ?? (await this.references()).idRole;
  }

  async sitesGroup(opts: { owner?: number; name?: string } = {}) {
    const { idModule } = await this.references();
    return this.create('sites_group', {
      sites_group_name: opts.name ?? uniqueName('grp'),
      sites_group_code: 'E2E',
      modules: [idModule],
      id_digitiser: await this.owner(opts.owner),
    });
  }

  async site(opts: { owner?: number; name?: string; idSitesGroup?: number } = {}) {
    const { idTypeSite } = await this.references();
    const owner = await this.owner(opts.owner);
    return this.create('site', {
      base_site_name: opts.name ?? uniqueName('site'),
      base_site_code: 'E2E', // requis dans le gestionnaire de sites
      id_sites_group: opts.idSitesGroup,
      types_site: [idTypeSite],
      id_inventor: owner,
      id_digitiser: owner,
      first_use_date: '2024-01-01',
      geom: { type: 'Point', coordinates: [3.6, 44.3] },
    });
  }

  async visit(idBaseSite: number, opts: { owner?: number; comments?: string } = {}) {
    const { idDataset } = await this.references();
    const owner = await this.owner(opts.owner);
    return this.create('visit', {
      id_base_site: idBaseSite,
      visit_date_min: '2024-01-01',
      id_dataset: idDataset,
      id_digitiser: owner,
      observers: [owner],
      comments: opts.comments ?? uniqueName('visit'),
    });
  }

  async observation(idBaseVisit: number, opts: { owner?: number; comments?: string } = {}) {
    const { cdNom } = await this.references();
    return this.create('observation', {
      id_base_visit: idBaseVisit,
      cd_nom: cdNom,
      id_digitiser: await this.owner(opts.owner),
      comments: opts.comments ?? uniqueName('obs'),
    });
  }

  async observationDetail(idObservation: number) {
    return this.create('observation_detail', { id_observation: idObservation });
  }

  async individual(opts: { owner?: number; name?: string } = {}) {
    const { cdNom } = await this.references();
    return this.create('individual', {
      individual_name: opts.name ?? uniqueName('indi'),
      cd_nom: cdNom,
      active: true,
      id_digitiser: await this.owner(opts.owner),
    });
  }

  async marking(idIndividual: number, opts: { owner?: number; code?: string } = {}) {
    const { idMarkingType } = await this.references();
    const owner = await this.owner(opts.owner);
    return this.create('marking', {
      id_individual: idIndividual,
      id_digitiser: owner,
      id_operator: owner,
      marking_date: '2024-01-01',
      marking_code: opts.code ?? uniqueName('mark'),
      id_nomenclature_marking_type: idMarkingType,
    });
  }
}

/** Données du sous-module (`GET /monitorings/module/<id>`) à partir de son code. */
export async function getModule(api: APIRequestContext, moduleCode: string) {
  const custom = (await (await api.get(`${REFACTO}/${moduleCode}/config`)).json()).custom;
  const res = await api.get(`${API}/monitorings/module/${custom['__MODULE.ID_MODULE']}`);
  if (!res.ok()) throw new Error(`module ${moduleCode}: HTTP ${res.status()}`);
  return res.json();
}

/** Modifie des propriétés du sous-module (même payload « à plat » que le formulaire). */
export async function patchModule(api: APIRequestContext, moduleCode: string, properties: Record<string, unknown>) {
  const m = await getModule(api, moduleCode);
  const keep = [
    'id_module', 'module_code', 'module_label', 'module_path', 'module_desc', 'module_picto',
    'uuid_module_complement', 'datasets', 'id_list_observer', 'id_list_taxonomy',
    'taxonomy_display_field_name', 'active_frontend', 'b_synthese', 'cd_nom',
  ];
  const payload: Record<string, unknown> = Object.fromEntries(keep.map((k) => [k, m[k]]));
  payload.types_site = (m.types_site ?? []).map((t: any) => t.id_nomenclature_type_site ?? t);
  Object.assign(payload, properties);
  const res = await api.patch(`${API}/monitorings/${moduleCode}/module/${m.id_module}`, { data: payload });
  if (!res.ok()) throw new Error(`PATCH module ${moduleCode}: HTTP ${res.status()} ${await res.text()}`);
  return res.json();
}

/**
 * Configure le sous-module s'il ne l'est pas (#752 : liste d'observateurs, jeu de données,
 * liste de taxons, affichage des taxons) avec les premières valeurs disponibles sur l'instance.
 */
export async function ensureModuleConfigured(api: APIRequestContext, moduleCode: string) {
  const config = await (await api.get(`${REFACTO}/${moduleCode}/config`)).json();
  if (config.configured !== false) return;
  const env = (k: string) => (process.env[k] ? Number(process.env[k]) : undefined);
  const idDataset =
    env('GN_ID_DATASET') ?? (await (await api.get(`${API}/meta/datasets?active=true`)).json())[0]?.id_dataset;
  const types = await (await api.get(`${API}/monitorings/sites/types`)).json();
  await patchModule(api, moduleCode, {
    datasets: [idDataset],
    id_list_observer: env('GN_ID_LIST_OBSERVER') ?? 1,
    id_list_taxonomy: env('GN_ID_LIST_TAXONOMY') ?? 100,
    taxonomy_display_field_name: 'nom_vern,lb_nom',
    types_site: [types.items[0].id_nomenclature_type_site],
    active_frontend: true,
    b_synthese: false,
  });
}

/**
 * Jeu de données dont l'utilisateur testé est acteur, rattaché aux sous-modules de test : au
 * scope 1/2 de création, seuls ces jeux sont proposés dans les formulaires (ex. visite).
 * Créé une fois (recherché par son nom), sur le modèle du 1er jeu de données du module.
 */
export async function ensureUserDataset(admin: APIRequestContext, identifiant: string, idRole: number) {
  const name = `e2e-dataset-${identifiant}`;
  const datasets: any[] = await (await admin.get(`${API}/meta/datasets?fields=dataset_name`)).json();
  const existing = datasets.find((d) => d.dataset_name === name);
  if (existing) return existing.id_dataset as number;

  const modules = await Promise.all([MODULE, MODULE_INDI].map((code) => getModule(admin, code)));
  const model = await (await admin.get(`${API}/meta/dataset/${modules[0].datasets[0]}`)).json();
  const res = await admin.post(`${API}/meta/dataset`, {
    data: {
      id_acquisition_framework: model.id_acquisition_framework,
      dataset_name: name,
      dataset_shortname: name,
      dataset_desc: 'Jeu de données de la recette E2E du module Monitoring',
      keywords: 'e2e',
      terrestrial_domain: true,
      marine_domain: false,
      active: true,
      validable: true,
      id_nomenclature_data_type: model.id_nomenclature_data_type,
      id_nomenclature_collecting_method: model.id_nomenclature_collecting_method,
      id_nomenclature_data_origin: model.id_nomenclature_data_origin,
      id_nomenclature_source_status: model.id_nomenclature_source_status,
      id_nomenclature_resource_type: model.id_nomenclature_resource_type,
      cor_dataset_actor: [
        { id_role: idRole, id_nomenclature_actor_role: model.cor_dataset_actor[0].id_nomenclature_actor_role },
      ],
      modules: modules.map((m) => ({ id_module: m.id_module, module_code: m.module_code, module_label: m.module_label })),
      cor_objectifs: [],
      cor_territories: [],
    },
  });
  if (!res.ok()) throw new Error(`POST dataset ${name}: HTTP ${res.status()} ${await res.text()}`);
  return (await res.json()).id_dataset as number;
}
