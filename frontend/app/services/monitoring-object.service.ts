import { MonitoringObject } from './../class/monitoring-object';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import { ConfigService } from './config.service';
import { DataMonitoringObjectService } from './data-monitoring-object.service';
import { DataUtilsService } from './data-utils.service';
import { Utils } from '../utils/utils';
import { mergeMap } from 'rxjs/operators';
import { Router } from '@angular/router';

@Injectable()
export class MonitoringObjectService {
  constructor(
    private _configService: ConfigService,
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _dataUtilsService: DataUtilsService,
    private _router: Router
  ) {}

  _cache = {};

  cache(moduleCode, objectType = null, id = null) {
    let cache = (this._cache[moduleCode] = this._cache[moduleCode] || {});

    if (!objectType) {
      return cache;
    }
    cache = cache[objectType] = cache[objectType] || {};

    if (objectType === 'module') {
      return cache;
    }

    if (id) {
      cache = cache[id] = cache[id] || null;
    }
    return cache;
  }

  setCache(obj: MonitoringObject, objData) {
    // post ou update

    if (obj.objectType === 'module' && !obj.moduleCode) {
      return;
    }
    if (obj.objectType !== 'module' && !obj.id) {
      return;
    }

    // object
    if (obj.objectType === 'module') {
      const cache = this.cache(obj.moduleCode);
      cache['module'] = objData;
    } else {
      const cache = this.cache(obj.moduleCode, obj.objectType);
      cache[obj.id] = objData;
    }

    // children
    if (objData.children) {
      for (const childrenType of Object.keys(objData.children)) {
        const childrenData = objData.children[childrenType];
        const cacheChildren = this.cache(obj.moduleCode, childrenType);
        for (const childData of childrenData) {
          cacheChildren[childData.id] = childData;
        }
      }
    }

    for (const parentType of obj.parentTypes()) {
      obj.getParent(parentType, 1).subscribe(() => {
        this.setParentCache(obj, objData, parentType);
      });
    }
  }

  setParentCache(obj: MonitoringObject, objData, parentType) {
    const parent = this.getParentFromCache(obj, parentType);
    if (parent) {
      const index = parent.children[obj.objectType].findIndex((child) => {
        return Number(child.id) === Number(obj.id);
      });

      if (index !== -1) {
        // update
        parent.children[obj.objectType].splice(index, 1, objData);
      } else {
        // post
        parent.children[obj.objectType].push(objData);

        // update nb_child
        const key = Object.keys(parent.properties).find((k) =>
          ['nb_visits', 'nb_observations', 'nb_sites', 'nb_sites_groups'].includes(k)
        );
        if (key) {
          console.log('up cache', parent.properties.base_site_name, key);
          parent.properties[key] = parent.children[obj.objectType].length;
        }
      }
    }
  }

  getParentFromCache(obj: MonitoringObject, parentType) {
    const parentData = this.cache(obj.moduleCode, parentType, obj.parentId(parentType));
    if (!(parentData && parentData.children)) {
      return;
    }
    return parentData ? parentData : null;
  }

  getFromCache(obj: MonitoringObject) {
    // get
    if (obj.objectType === 'module' && !obj.moduleCode) {
      return;
    }
    if (obj.objectType !== 'module' && !obj.id) {
      return;
    }

    const objData = this.cache(obj.moduleCode, obj.objectType, obj.id);

    if (!(objData && Object.keys(objData).length)) {
      return null;
    }

    if (obj.childrenTypes().length && !objData.children) {
      return null;
    }

    return objData;
  }

  deleteCache(obj: MonitoringObject) {
    let index: Number;
    // children
    for (const childrenType of obj.childrenTypes()) {
      const childrenData = obj.children[childrenType] || [];
      for (const childData of childrenData) {
        const child = new MonitoringObject(obj.moduleCode, childrenType, childData.id, this);
        this.deleteCache(child);
      }
    }

    // parents
    // TODO cas update on change id_sites_group (tester tous les sites_groups??)
    for (const parentType of obj.parentTypes()) {
      const parent = this.getParentFromCache(obj, parentType);
      if (parent && Object.keys(parent).length) {
        index = parent.children[obj.objectType].findIndex((child) => {
          return Number(child.id) === Number(obj.id);
        });
        parent.children[obj.objectType].splice(index, 1);
        // update nb_child
        const key = Object.keys(parent.properties).find((k) =>
          ['nb_visits', 'nb_observations', 'nb_sites'].includes(k)
        );
        if (key) {
          parent.properties[key] = parent.children[obj.objectType].length;
        }
      }
    }

    // delete
    const objectsCache = this.cache(obj.moduleCode, obj.objectType);
    delete objectsCache[obj.id];
  }

  configUtils(elem, moduleCode) {
    return this._configService.config()[moduleCode].display_field_names[elem.type_util];
  }

  toForm(elem, val): Observable<any> {
    let x = val;
    // valeur par default depuis la config schema
    x = [undefined, null].includes(x) ? elem.value || null : x;

    switch (elem.type_widget) {
      case 'date': {
        const date = new Date(x);
        x = x
          ? {
              year: date.getUTCFullYear(),
              month: date.getUTCMonth() + 1,
              day: date.getUTCDate(),
            }
          : null;
        break;
      }
      case 'observers': {
        // For performance reasons, filter on Set instead of Array
        let registeredObservers = new Set();
        if (elem.multi_select === true) {
          if (!Array.isArray(x) || x.length == 0) {
            x = [];
            break;
          }
          registeredObservers = new Set(x);
        } else {
          registeredObservers.add(x);
        }

        x = this._dataUtilsService.getUsersByCodeList(this._configService.codeListObservers()).pipe(
          mergeMap((users: any) => {
            let observers: any = [];
            users.forEach((user) => {
              if (registeredObservers.has(user.id_role)) {
                if (elem.multi_select === true) {
                  observers.push(user);
                } else {
                  observers = [user];
                  return;
                }
              }
            });
            return of(observers);
          })
        );
        break;
      }
      case 'taxonomy': {
        x = x ? this._dataUtilsService.getUtil('taxonomy', x, 'all') : null;
        break;
      }
    }

    if (
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
    switch (elem.type_widget) {
      case 'date': {
        x = x && x.year && x.month && x.day ? `${x.year}-${x.month}-${x.day}` : null;
        break;
      }
      case 'observers': {
        x = x.map((user) => user.id_role);
        if (elem.multi_select === false) {
          x = x[0];
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

  dateFromString(s_date) {
    const v_date = s_date.split('/');
    if (v_date.length !== 3) {
      return null;
    }
    const date = Date.parse(`${v_date[2]}-${v_date[1]}-${v_date[0]}`);
    return date;
  }

  numberFromString(s) {
    const v = s.split(' ');
    const s_n = v[0];
    const v_n = s_n.split('.');
    v_n[0] = Number(v_n[0]);
    v_n[1] = Number(v_n[1]);
    return v_n.length > 1 && v_n[0] ? v_n : null;
  }

  dataMonitoringObjectService(): DataMonitoringObjectService {
    return this._dataMonitoringObjectService;
  }

  dataUtilsService(): DataUtilsService {
    return this._dataUtilsService;
  }

  configService(): ConfigService {
    return this._configService;
  }

  navigate(routeType, moduleCode, objectType, id, queryParams = {}) {
    let editParams = '';
    if ('edit' in queryParams && queryParams.edit == true) {
      editParams = 'true';
      delete queryParams.edit;
    }

    this._router.navigate(
      [
        this._configService.frontendModuleMonitoringUrl(),
        routeType,
        moduleCode,
        objectType,
        id,
        { edit: editParams },
      ].filter((s) => !!s),
      {
        queryParams,
      }
    );
  }
}
