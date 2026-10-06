
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import { ConfigService } from './config.service';
import { DataUtilsService } from './data-utils.service';
import { Utils } from '../utils/utils';
import { mergeMap } from 'rxjs/operators';

@Injectable()
export class MonitoringObjectService {
  constructor(
    private _configService: ConfigService,
    private _dataUtilsService: DataUtilsService,
  ) {}




  toForm(elem, val): Observable<any> {
    let x = val;
    // valeur par default depuis la config schema
    x = [undefined, null].includes(x) ? (elem.value === '' ? null : elem.value) : x;
    if (elem.type_widget == 'date') {
      const date = new Date(x);
      x = x
        ? {
            year: date.getUTCFullYear(),
            month: date.getUTCMonth() + 1,
            day: date.getUTCDate(),
          }
        : null;
    } else if (elem.type_widget === 'observers') {
      const codeListObservers = this._configService.codeListObservers();
      // Gestion des observateurs multiples
      if (!Array.isArray(val)) val = [val];

      x == null
        ? (x = [])
        : (x = this._dataUtilsService.getUsersByCodeList(codeListObservers).pipe(
            // Cas des observateurs multiples à gérer
            mergeMap((users: any) => {
              let currentUser = [];
              if (!Array.isArray(users)) {
                return of(null);
              }
              for (const user of users) {
                for (const obs of val) {
                  if (user.id_role == obs) {
                    currentUser.push(user);
                  }
                }
              }
              //Si non multiple on renvoie le premier élément ou null
              if (!elem.multi_select) {
                currentUser = currentUser.length ? currentUser[0] : null;
              }
              return of(currentUser);
            })
          ));
    } else if (elem.type_widget === 'taxonomy') {
      x = x ? this._dataUtilsService.getUtil('taxonomy', x, 'all') : null;
    } else if (
      elem.type_util === 'nomenclature' &&
      Utils.isObject(x) &&
      x.code_nomenclature_type &&
      x.cd_nomenclature
    ) {
      x = this._dataUtilsService.getNomenclature(x.code_nomenclature_type, x.cd_nomenclature).pipe(
        mergeMap((nomenclature) => {
          return of(nomenclature['id_nomenclature']);
        })
      );
    }

    x = x instanceof Observable ? x : of(x);
    return x;
  }

  fromForm(elem, val) {
    let x = val;
    if (x == undefined) {
      return x;
    }
    switch (elem.type_widget) {
      case 'date': {
        x =
          x && x.year && x.month && x.day
            ? `${x.year}-${String(x.month).padStart(2, '0')}-${String(x.day).padStart(2, '0')}`
            : null;
        break;
      }
      case 'observers': {
        if ('multi_select' in elem && elem.multi_select) {
          x = x.map((item) => {
            return item.id_role;
          });
        } else {
          x = x instanceof Array && x.length === 1 ? x[0].id_role : x.id_role;
        }
        break;
      }
      case 'taxonomy': {
        x = x instanceof Object ? x.cd_nom : x;
        break;
      }
    }
    return x;
  }

}
