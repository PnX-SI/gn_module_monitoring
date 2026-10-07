import { Observable, forkJoin, of } from 'rxjs';
import { map, concatMap, mergeMap } from 'rxjs/operators';
import { JsonData } from '../types/jsondata';

export class Utils {
  /** Fonction pour copier un objet de type dictionnaire */
  static copy(object) {
    if ([undefined].includes(object)) {
      return object;
    }
    return JSON.parse(JSON.stringify(object));
  }

  static isObject(x) {
    return typeof x === 'object' && x != null;
  }

  static formatDate(val) {
    // return val ? new Date(val).toLocaleString('fr-FR', { timeZone: 'UTC' }).replace(',', '').split(' ')[0] : val;
    return val ? val.split('-').reverse().join('/') : val;
  }
}

export function resolveObjectProperties(
  data,
  fieldsConfig,
  _configService,
  _cacheService
): Observable<any> {
  /**
   * Traite et résout les propriétés d'un ensemble de données en fonction des types de champs définis dans la configuration.
   *   La résolution consiste à transformer la valeur retournée par l'api par celle d'affichage
   *
   *
   * @param data - Données à traiter.
   * @param fieldsConfig - Configuration des champs permettant la résolution de chaque propriété.
   * @param moduleCode - Le code de module courant
   * @param _configService - Service utilisé pour la résolution des propriétés d'objet.
   * @param _cacheService - Service utilisé pour la mise en cache des propriétés résolues.
   * @returns Un observable émettant l'objet de données avec les propriétés résolues.
   */
  if ((!data || !fieldsConfig) && Object.keys(fieldsConfig).length > 0) {
    return of(data);
  }

  const propertyObservables = {};
  // si des données sont contenues dans dataItem.data merge avec dataItem
  // cas des propriétés supplémentaires des visites
  // TODO reflechir si on garde cette propriété ou si on met tout à plat dans dataItem
  if (data.data) {
    data = { ...data, ...data.data };
  }

  for (const attribut_name of Object.keys(fieldsConfig)) {
    if (data.hasOwnProperty(attribut_name)) {
      propertyObservables[attribut_name] = resolveProperty(
        _configService,
        _cacheService,
        fieldsConfig[attribut_name],
        data[attribut_name]
      );
    }
  }
  if (Object.keys(propertyObservables).length === 0) {
    return of(data);
  }
  return forkJoin(propertyObservables).pipe(
    map((resolvedProperties) => {
      const updatedSiteGroupItem = { ...data };
      for (const attribut_name of Object.keys(resolvedProperties)) {
        updatedSiteGroupItem[attribut_name] = resolvedProperties[attribut_name];
      }
      return updatedSiteGroupItem;
    })
  );
}

export function buildObjectResolvePropertyProcessing(
  data,
  fieldsConfig,
  _configService,
  _cacheService
): Observable<any> {
  /**
   * Traite et résout les propriétés d'un ensemble de données en fonction des types de champs définis dans la configuration.
   *   La résolution consiste à transformer la valeur retournée par l'api par celle d'affichage
   *
   *
   * @param data - Données à traiter.
   * @param fieldsConfig - Configuration des champs permettant la résolution de chaque propriété.
   * @param _configService - Service utilisé pour la résolution des propriétés d'objet.
   * @param _cacheService - Service utilisé pour la mise en cache des propriétés résolues.
   * @returns Un observable émettant l'objet de données avec les propriétés résolues.
   */

  const dataProcessing$ =
    data &&
    data.items &&
    data.items.length > 0 &&
    fieldsConfig &&
    Object.keys(fieldsConfig).length > 0
      ? forkJoin(
          data.items.map((dataItem: {}) => {
            return resolveObjectProperties(dataItem, fieldsConfig, _configService, _cacheService);
          })
        ).pipe(
          map((resolvedSiteGroupItems) => ({
            ...data,
            items: resolvedSiteGroupItems,
          }))
        )
      : of(data);
  return dataProcessing$;
}

export function resolveProperty(_configService, _cacheService, elem, val): Observable<any> {
  if (elem.type_widget === 'date' || (elem.type_util === 'date' && val)) {
    val = Utils.formatDate(val);
  }
  if (elem.type_util === 'types_site') {
    const typesSite = (_configService.config()['module'] || [])['types_site'];
    val = val.map((item) => {
      return typesSite[item]?.name;
    });
  }
  const fieldName = (_configService.config()['display_field_names'] || [])[elem.type_util];

  if (val && fieldName && elem.type_widget) {
    return getUtil(_cacheService, elem.type_util, val, fieldName, elem.value_field_name);
  }

  return of(val);
}

// TODO en doublon avec getUtil de DataUtilsService
function getUtil(
  _cacheService,
  typeUtil: string,
  id,
  fieldName: string,
  idFieldName: string | null = null
) {
  if (Array.isArray(id)) {
    return getUtils(_cacheService, typeUtil, id, fieldName, idFieldName);
  }

  var urlRelative = `util/${typeUtil}/${id}`;

  var isGN2Route = false;
  if (typeUtil == 'user') {
    var urlRelative = `users/role/${id}`;
    var isGN2Route = true;
  }

  if (idFieldName) {
    urlRelative += `?id_field_name=${idFieldName}`;
  }

  const sCachePaths = `util|${typeUtil}|${id}`;

  return _cacheService.cache_or_request('get', urlRelative, sCachePaths, isGN2Route).pipe(
    mergeMap((value) => {
      let out;
      if (fieldName === 'all') {
        out = value;
      } else if (fieldName.split(',').length >= 2) {
        for (const fieldNameInter of fieldName.split(',')) {
          if (value[fieldNameInter]) {
            out = value[fieldNameInter];
            break;
          }
        }
      } else {
        out = value[fieldName];
      }
      return of(out);
    })
  );
}

// TODO en doublon avec getUtils de DataUtilsService
function getUtils(_cacheService, typeUtilObject, ids, fieldName, idFieldName) {
  if (!ids.length) {
    return of(null);
  }
  const observables: any[] = [];

  for (const id of ids) {
    observables.push(getUtil(_cacheService, typeUtilObject, id, fieldName, idFieldName));
  }

  return forkJoin(observables).pipe(
    concatMap((res) => {
      return of(res.join(', '));
    })
  );
}
