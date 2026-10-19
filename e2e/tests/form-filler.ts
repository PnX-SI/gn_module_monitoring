import { APIRequestContext, Page, Locator } from '@playwright/test';
import { selectNgOption } from './helpers';

export const API = process.env.GN_API_URL ?? 'http://127.0.0.1:8000';

export type FieldDef = {
  type_widget?: string;
  required?: boolean | string;
  hidden?: boolean | string;
  [k: string]: unknown;
};
export type ObjectConfig = { fields: Record<string, FieldDef>; [k: string]: unknown };

/** Merged (generic + protocol `specific`) config, as consumed by the Angular forms. */
export async function getModuleConfig(request: APIRequestContext, moduleCode: string) {
  const res = await request.get(`${API}/monitorings/refacto/${moduleCode}/config`);
  if (!res.ok()) throw new Error(`config ${moduleCode}: HTTP ${res.status()}`);
  return res.json() as Promise<Record<string, any>>;
}

/** Site types (admin "Types de sites"): may carry their own `config.specific` fields. */
export async function getSiteTypes(request: APIRequestContext) {
  const res = await request.get(`${API}/monitorings/sites/types`);
  return (await res.json()).items as { id_nomenclature_type_site: number; label: string; config: any }[];
}

/**
 * Fields to fill: statically required (`required: true`) and not statically hidden.
 * `hidden` JS expressions are resolved by the UI: `fillField` skips fields that are not
 * visible. JS-expression `required` (conditional on other values) is not handled here:
 * pass those through `overrides`/explicit `fillField` calls.
 */
export function requiredFieldNames(fields: Record<string, FieldDef>): string[] {
  return Object.entries(fields)
    .filter(([, d]) => d.required === true && d.hidden !== true)
    .map(([name]) => name);
}

/** data-qa is `field-<widget>-<name>`, except datalists which use `field-datalist-<label>-<name>`. */
export const fieldByName = (page: Page, name: string): Locator =>
  page.locator(`[data-qa^="field-"][data-qa$="-${name}"]`).first();

/**
 * Fill one field according to its `type_widget`. `value` is used for free inputs; for
 * choice widgets it is an optional option text (default: first option).
 */
export async function fillField(page: Page, name: string, def: FieldDef, value?: string | number) {
  const host = fieldByName(page, name);
  // wait for the dynamic form to render the field; absent => not part of this form
  const attached = await host.waitFor({ state: 'attached', timeout: 5_000 }).then(() => true, () => false);
  if (!attached || !(await host.isVisible())) return; // absent or hidden by config
  const widget = def.type_widget ?? 'text';
  switch (widget) {
    case 'text':
    case 'textarea':
    case 'number':
    case 'time':
      if (value === undefined && (await host.inputValue())) break; // keep defaults
      await host.fill(String(value ?? (widget === 'number' ? 1 : `e2e-${name}`)));
      break;
    case 'date': {
      const input = host.locator('input').first();
      if (!(await input.inputValue()) || value) {
        await input.fill(String(value ?? '01/01/2024')); // dd/mm/yyyy
        await input.blur(); // commit the value to the datepicker model
      }
      break;
    }
    case 'select': {
      // `select` is a native <select> (not ng-select): first real option unless a label is given
      const isSelect = await host.evaluate((e) => e.tagName === 'SELECT');
      const native = isSelect ? host : host.locator('select');
      if (value) await native.selectOption({ label: String(value) });
      else await native.selectOption({ index: 1 });
      break;
    }
    case 'observers':
    case 'observers-text':
    case 'dataset':
    case 'nomenclature':
    case 'datalist':
    case 'taxonomy':
    case 'multiselect': {
      const target = (await host.locator('input').count()) ? host.locator('input').first() : host;
      // keep a pre-filled value (e.g. current user as observer)
      if (await host.locator('.ng-value').count()) return;
      if (widget === 'taxonomy') {
        // taxon list is searched server side: type, wait for options, take the first
        // no hardcoded taxon: take the first one of the list configured on the field (`id_list`)
        if (!value) {
          const res = await page.request.get(`${API}/taxhub/api/taxref/allnamebylist/${def.id_list}?limit=1`);
          value = (await res.json())[0]?.lb_nom;
          if (!value) throw new Error(`taxon list ${def.id_list} is empty`);
        }
        await target.click();
        await target.pressSequentially(String(value));
        // the taxon widget is an ngb typeahead (not an ng-select)
        const suggestion = page.locator('ngb-typeahead-window .dropdown-item').first();
        await suggestion.waitFor({ state: 'visible' });
        await suggestion.click();
      } else {
        if (value) {
          // long lists are paginated: filter by typing before picking the option
          await target.click();
          await target.pressSequentially(String(value));
        }
        await selectNgOption(page, target, value ? String(value) : undefined);
      }
      break;
    }
    case 'bool_checkbox':
      await host.check();
      break;
    default:
      // medias, html, individuals... not required in practice; extend when a protocol needs it
      break;
  }
}

/** Fill every statically-required field of an object config. */
export async function fillRequired(
  page: Page,
  config: ObjectConfig,
  overrides: Record<string, string | number> = {},
) {
  for (const name of requiredFieldNames(config.fields)) {
    await fillField(page, name, config.fields[name], overrides[name]);
  }
}

/** Fields declared in the `specific` block of a site type config (if any), required only. */
export function siteTypeRequiredFields(typeConfig: any): Record<string, FieldDef> {
  const specific = typeConfig?.specific ?? {};
  return Object.fromEntries(
    Object.entries<FieldDef>(specific).filter(([, d]) => d.required === true && d.hidden !== true),
  );
}
