import { Observable } from '@librairies/rxjs/Observable';


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
    return val ? new Date(val).toLocaleString('fr-FR', { timeZone: 'UTC' }).replace(',', '').split(' ')[0] : val;
  }

  static mapDictToArray(dictIn: Object, processFunc= null, fieldName: string = null): Array<any> {
    if (!dictIn) {
      return null;
    }
    const arrayOut = [];
    return Object.keys(dictIn).map((key) => {
      let elem = dictIn[key];
      const condKey = Utils.isObject(elem) && fieldName;
      if ( condKey ) {
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
  static mapArrayToDict(arrayIn: Array<any>, processFunc= null, fieldName: string = null): Object {
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

}
