import { Observable } from "@librairies/rxjs/Observable";


export class Utils {

  /** Fonction pour copier un objet de type dictionnaire */
  static copy(object) {
    return JSON.parse(JSON.stringify(object));
  }

  static dictSize(dict) {
    return Object.keys(dict).length;
  }

  static isObject(x) {
    return typeof x === 'object' && x != null;
  }

  static formatDate(val) {
    return val ? new Date(val).toLocaleString('fr-FR', { timeZone: 'UTC' }).split(' ')[0] : val
  }

  static mapDictToArray(dictIn: Object, processFunc=null, fieldName: string = null): Array<any> {
    if (!dictIn) {
      return null;
    }
    let arrayOut = [];
    return Object.keys(dictIn).map((key) => {
      let elem = dictIn[key];
      let condKey = Utils.isObject(elem) && fieldName;
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
  static mapArrayToDict(arrayIn: Array<any>, processFunc=null, fieldName: string = null): Object {
    if (!arrayIn) {
      return null;
    }
    let dictOut = {};
      arrayIn.forEach((elem) => {
        let condKey = Utils.isObject(elem) && fieldName in elem;
        let key = condKey ? elem[fieldName]: elem;
        dictOut[key] = processFunc ? processFunc(elem) : elem;
      });
    return dictOut;
  }

}
