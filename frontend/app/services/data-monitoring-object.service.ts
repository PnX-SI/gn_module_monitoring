import { Observable } from 'rxjs';
import { Injectable } from "@angular/core";

import { CacheService } from "./cache.service";

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
    return this._cacheService.request('get', `modules`)
  }

  // /**
  //  * Renvoie un module référencé par le champ module_path
  //  * 
  //  * @param modulePath le champ module_path du module
  //  */
  // getModule(modulePath) {
  //   return this._cacheService.request('get', `module/${modulePath}`)
  // }

  /** Object */
  urlMonitoring(apiType, modulePath, objectType, id=null, depth=null) {
    
    let url: string;
    let params = {}
    if(objectType.includes('module')) {
      url = modulePath ? `${apiType}/${modulePath}/${objectType}` : `${apiType}/module`;
      params['field_name'] = 'module_path'
    } else {
      url = id ? `${apiType}/${modulePath}/${objectType}/${id}` : `${apiType}/${modulePath}/${objectType}`
    }

    if(depth) {
      params['depth'] = depth;
    }

    let s_params = Object.keys(params).map( key => `${key}=${params[key]}` ).join('&')
    url = s_params.length ? url + '?' + s_params  : url
    
    return url;
  }

  /**
   * Renvoie un objet pour un module, un type d'objet et un identifiant donnés
   * 
   * @param modulePath le champ module_path du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  getObject(modulePath, objectType, id=null, depth=null) {
    const url = this.urlMonitoring('object', modulePath, objectType, id, depth)
    return this._cacheService.request('get', url);
  }


  /**
   * Modifie un objet pour un module, un type d'objet et un identifiant donnés
   * 
   * @param modulePath le champ module_path du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  patchObject(modulePath, objectType, id, postData) {
    const url = this.urlMonitoring('object', modulePath, objectType, id)
    return this._cacheService.request('patch', url, postData);
  }


  /**
   *  Créé un objet pour un module, un type d'objet
   * 
   * @param modulePath le champ module_path du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  postObject(modulePath, objectType, postData) {
    const url = this.urlMonitoring('object', modulePath, objectType)
    return this._cacheService.request('post', url, postData);
  }


  /**
   * Supprime un objet pour un module, un type d'objet et un identifiant donnés
   * 
   * @param modulePath le champ module_path du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  deleteObject(modulePath, objectType, id) {
    const url = this.urlMonitoring('object', modulePath, objectType, id)
    return this._cacheService.request('delete', url);
  }


  // /**
  //  *  
  //  * Renvoie une liste d'objet pour un module, un type d'objet 
  //  *  et un identifiant du parent de l'objet donnés
  //  * 
  //  * @param modulePath le champ module_path du module
  //  * @param objectType le type de l'objet (site, visit, observation, ...)
  //  * @param idParent identidiant du parent de l'objet
  //  */
  // getObjects(modulePath, objectType, idParent) {
  //   return this._cacheService.request('get', `objects/${modulePath}/${objectType}/${idParent}`);
  // }

  /** Breadcrumps */
  /** 
   * Renvoie le fil d'ariane d'un object
   * 
   * @param modulePath le champ module_path du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
  */
  getBreadcrumps(modulePath, objectType, id) {
    let url = this.urlMonitoring('breadcrumps', modulePath, objectType, id)
    return this._cacheService.request('get', url);
  }

 
  getCircuitPoints(idCircuit): Observable<Array<any>> {
    let url = 'circuit_points/' +  idCircuit;
    return this._cacheService.request('get', url);
  }
  

}
