import { Observable } from 'rxjs/Observable';
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
