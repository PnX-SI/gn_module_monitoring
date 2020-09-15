import { mergeMap } from '@librairies/rxjs/operators';
import { Observable, of } from '@librairies/rxjs';
import { Injectable } from '@angular/core';

import { CacheService } from './cache.service';

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class DataMonitoringObjectService {

  constructor(private _cacheService: CacheService) { }

  /** Modules */

  /**
   * Renvoie la liste des modules
   */
  getModules() {
    return this._cacheService.request('get', `modules`);
  }

  // /**
  //  * Renvoie un module référencé par le champ module_code
  //  *
  //  * @param moduleCode le champ module_code du module
  //  */
  // getModule(moduleCode) {
  //   return this._cacheService.request('get', `module/${moduleCode}`)
  // }

  /** Object */
  urlMonitoring(apiType, moduleCode, objectType, id = null, depth = null) {

    let url: string;
    const params = {};
    if (objectType.includes('module')) {
      url = moduleCode ? `${apiType}/${moduleCode}/${objectType}` : `${apiType}/module`;
      params['field_name'] = 'module_code';
    } else {
      url = id ? `${apiType}/${moduleCode}/${objectType}/${id}` : `${apiType}/${moduleCode}/${objectType}`;
    }

    if (depth) {
      params['depth'] = depth;
    }

    const s_params = Object.keys(params).map(key => `${key}=${params[key]}`).join('&');
    url = s_params.length ? url + '?' + s_params : url;

    return url;
  }


  /**
   * Renvoie un objet pour un module, un type d'objet et un identifiant donnés
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  getObject(moduleCode, objectType, id = null, depth = null) {
    const url = this.urlMonitoring('object', moduleCode, objectType, id, depth);
    return this._cacheService.request('get', url);
  }


  /**
   * Modifie un objet pour un module, un type d'objet et un identifiant donnés
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  patchObject(moduleCode, objectType, id, postData) {
    const url = this.urlMonitoring('object', moduleCode, objectType, id);
    return this._cacheService.request('patch', url, postData);
  }


  /**
   *  Créé un objet pour un module, un type d'objet
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  postObject(moduleCode, objectType, postData) {
    const url = this.urlMonitoring('object', moduleCode, objectType);
    return this._cacheService.request('post', url, postData);
  }


  /**
   * Supprime un objet pour un module, un type d'objet et un identifiant donnés
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  deleteObject(moduleCode, objectType, id) {
    const url = this.urlMonitoring('object', moduleCode, objectType, id);
    return this._cacheService.request('delete', url);
  }


  // /**
  //  *
  //  * Renvoie une liste d'objet pour un module, un type d'objet
  //  *  et un identifiant du parent de l'objet donnés
  //  *
  //  * @param moduleCode le champ module_code du module
  //  * @param objectType le type de l'objet (site, visit, observation, ...)
  //  * @param idParent identidiant du parent de l'objet
  //  */
  // getObjects(moduleCode, objectType, idParent) {
  //   return this._cacheService.request('get', `objects/${moduleCode}/${objectType}/${idParent}`);
  // }

  /** breadcrumbs */
  /**
   * Renvoie le fil d'ariane d'un object
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
  */
  getbreadcrumbs(moduleCode, objectType, id) {
    const url = this.urlMonitoring('breadcrumbs', moduleCode, objectType, id);
    return this._cacheService.request('get', url);
  }

}
