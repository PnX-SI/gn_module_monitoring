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

  static equal(x1, x2) {
    return JSON.stringify(x1) === JSON.stringify(x2);
  }

  static dictSize(dict) {
    return Object.keys(dict).length;
  }

  static isObject(x) {
    return typeof x === 'object' && x != null;
  }

  static formatDate(val) {
    // return val ? new Date(val).toLocaleString('fr-FR', { timeZone: 'UTC' }).replace(',', '').split(' ')[0] : val;
    return val ? val.split('-').reverse().join('/') : val;
  }

  static mapDictToArray(dictIn: Object, processFunc = null, fieldName: string = null): Array<any> {
    if (!dictIn) {
      return null;
    }
    const arrayOut = [];
    return Object.keys(dictIn).map((key) => {
      let elem = dictIn[key];
      const condKey = Utils.isObject(elem) && fieldName;
      if (condKey) {
        elem[fieldName] = key;
      }
      elem = processFunc ? processFunc(elem) : elem;
      return elem;
    });
  }

  /** transforme arrayIn en dictOut
   * (opt) processFunc modifie les elements de arrayIn
   * (opt) field name pour prendre comme cle du dictOut elem[field_name]
   */
  static mapArrayToDict(arrayIn: Array<any>, processFunc = null, fieldName: string = null): Object {
    if (!arrayIn) {
      return null;
    }
    const dictOut = {};
    arrayIn.forEach((elem) => {
      const condKey = Utils.isObject(elem) && fieldName in elem;
      const key = condKey ? elem[fieldName] : elem;
      dictOut[key] = processFunc ? processFunc(elem) : elem;
    });
    return dictOut;
  }

  static toObject(keys, values) {
    const obj = keys.reduce((accumulator, key, index) => {
      return { ...accumulator, [key]: values[key] };
    }, {});

    return obj;
  }

  static getRemainingProperties(obj1: JsonData, obj2: JsonData): JsonData {
    const remainingObj: JsonData = {};
    for (let key in obj1) {
      if (!obj2.hasOwnProperty(key) || obj1[key] !== obj2[key]) {
        remainingObj[key] = obj1[key];
      }
    }
    for (let key in obj2) {
      if (!obj1.hasOwnProperty(key) || obj1[key] !== obj2[key]) {
        remainingObj[key] = obj2[key];
      }
    }

    return remainingObj;
  }

  static getRemainingKeys(obj1, obj2): JsonData {
    const remainingKeys = {};

    // Iterate through the keys of obj1
    for (const key in obj1) {
      // Check if the key does not exist in obj2
      if (!(key in obj2)) {
        // Add the key and its value to the remainingKeys object
        remainingKeys[key] = obj1[key];
      }
    }

    return remainingKeys;
  }

  static mergeObjects(obj1: JsonData, obj2: JsonData): JsonData {
    const mergedObject: JsonData = { ...obj1 };
    for (const key in obj2) {
      if (obj2.hasOwnProperty(key)) {
        mergedObject[key] = obj2[key];
      }
    }

    return mergedObject;
  }

  static filterObject(objToFilt: JsonData, arrayUseToFilt: (string | number)[]): JsonData {
    const keysToFilter: (string | number)[] = arrayUseToFilt.map(String) as (string | number)[];
    const filteredObject = Object.keys(objToFilt).reduce((obj, key) => {
      if (keysToFilter.includes(key)) {
        obj[key] = objToFilt[key];
      }
      return obj;
    }, {});
    return filteredObject;
  }
}

export function buildObjectResolvePropertyProcessing(
  data,
  specificConfig,
  moduleCode,
  _objService,
  _cacheService,
  _configService
) {
  const fieldsConfig = _configService.schema(moduleCode, 'site');
  const dataProcessing$ =
    data &&
    data.items &&
    data.items.length > 0 &&
    specificConfig &&
    Object.keys(specificConfig).length > 0
      ? forkJoin(
          data.items.map((dataItem) => {
            const propertyObservables = {};
            for (const attribut_name of Object.keys(fieldsConfig)) {
              if (dataItem.hasOwnProperty(attribut_name)) {
                propertyObservables[attribut_name] = resolveProperty(
                  _objService,
                  _cacheService,
                  _configService,
                  moduleCode,
                  fieldsConfig[attribut_name],
                  dataItem[attribut_name]
                );
              }
            }
            if (Object.keys(propertyObservables).length === 0) {
              return of(dataItem);
            }
            return forkJoin(propertyObservables).pipe(
              map((resolvedProperties) => {
                const updatedSiteGroupItem = { ...dataItem };
                for (const attribut_name of Object.keys(resolvedProperties)) {
                  updatedSiteGroupItem[attribut_name] = resolvedProperties[attribut_name];
                }
                return updatedSiteGroupItem;
              })
            );
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

export function resolveProperty(
  _objService,
  _cacheService,
  _configService,
  moduleCode,
  elem,
  val
): Observable<any> {
  if (elem.type_widget === 'date' || (elem.type_util === 'date' && val)) {
    val = Utils.formatDate(val);
  }
  if (elem.type_util === 'types_site') {
    val = val.map((item) => {
      return item.label;
    });
  }

  const fieldName = _objService.configUtils(elem, moduleCode);
  if (val && fieldName && elem.type_widget) {
    return getUtil(_cacheService, elem.type_util, val, fieldName, elem.value_field_name);
  }

  return of(val);
}

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

  if (idFieldName) {
    urlRelative += `?id_field_name=${idFieldName}`;
  }

  const sCachePaths = `util|${typeUtil}|${id}`;

  return _cacheService.cache_or_request('get', urlRelative, sCachePaths).pipe(
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
