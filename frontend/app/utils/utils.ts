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
