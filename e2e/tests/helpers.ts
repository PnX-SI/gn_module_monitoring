import { Page, Locator, expect } from '@playwright/test';

export const MONITORING_URL = '/#/monitorings';
export const GENERIC = 'generic'; // pseudo-module "Gestionnaire de sites"

/** Unique, recognisable test data name. */
export const uniqueName = (prefix: string) => `e2e-${prefix}-${Date.now()}`;

/** Dynamic form fields carry `data-qa="field-<widget>-<attribut_name>"`. */
export const field = (page: Page, widget: string, name: string): Locator =>
  page.locator(`[data-qa="field-${widget}-${name}"]`);

export const submitButton = (page: Page) =>
  page.getByRole('button', { name: 'Valider', exact: true });

/** Open a new-style (-g components) list page: object/<module>/<objectType>. */
export async function gotoList(page: Page, moduleCode: string, objectType: string) {
  await page.goto(`${MONITORING_URL}/object/${moduleCode}/${objectType}`);
  await expect(page.locator('ngx-datatable')).toBeVisible();
}

/** Pick an option of an ng-select based widget (options live in a global overlay). */
export async function selectNgOption(page: Page, select: Locator, optionText?: string | RegExp) {
  await select.click();
  const anyOption = page.locator('.ng-option').first();
  await anyOption.waitFor({ state: 'visible' }); // options may be loaded asynchronously
  if (typeof optionText === 'string') {
    await page.locator('.ng-option', { hasText: optionText }).first().click();
  } else {
    // ng-select highlights the first option when opened; Enter picks it. More stable than
    // clicking in a virtual-scrolled panel.
    await page.keyboard.press('Enter');
  }
  await page.keyboard.press('Escape');
}

/** Extract the numeric id of the object from a detail URL (`.../sites_group/38;edit=...`). */
export function idFromUrl(url: string, objectType: string): number {
  const m = url.match(new RegExp(`/${objectType}/(\\d+)`));
  if (!m) throw new Error(`No ${objectType} id in ${url}`);
  return Number(m[1]);
}

/** Confirm the "Attention ... Confirmer la suppression" modal. */
export async function confirmDelete(page: Page) {
  await page.getByRole('button', { name: 'Confirmer la suppression' }).click();
}

/**
 * Draw a geometry on the Leaflet map according to the object's `geometry_type` config
 * (string or list: first allowed type wins). Needed for geolocated objects (sites, ...):
 * the submit button stays disabled until a geometry exists ("Veuillez saisir une géométrie").
 */
export async function drawGeometry(page: Page, geometryType: string | string[] = 'Point') {
  const type = Array.isArray(geometryType) ? geometryType[0] : geometryType;
  const tool = { Point: 'marker', LineString: 'polyline', Polygon: 'polygon' }[type];
  if (!tool) throw new Error(`Unsupported geometry type: ${type}`);
  await page.locator(`.leaflet-draw-draw-${tool}`).click();
  const box = (await page.locator('.leaflet-container').first().boundingBox())!;
  const at = (dx: number, dy: number) => ({ x: box.x + box.width / 2 + dx, y: box.y + box.height / 2 + dy });
  const click = (p: { x: number; y: number }) => page.mouse.click(p.x, p.y);
  if (type === 'Point') {
    await click(at(0, 0));
  } else if (type === 'LineString') {
    await click(at(-40, 0));
    await click(at(40, 0));
    await page.mouse.dblclick(at(40, 0).x, at(40, 0).y); // double click finishes the line
  } else {
    await click(at(-40, -30));
    await click(at(40, -30));
    await click(at(0, 40));
    await click(at(-40, -30)); // closing on the first vertex finishes the polygon
  }
}
