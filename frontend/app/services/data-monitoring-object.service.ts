import { mergeMap } from 'rxjs/operators';
import { Observable, of } from 'rxjs';
import { Injectable } from '@angular/core';

import { CacheService } from './cache.service';
import { ConfigService } from './config.service';
import { HttpClient } from '@angular/common/http';

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class DataMonitoringObjectService {
  constructor(
    private _cacheService: CacheService,
    private _http: HttpClient,
    private _config: ConfigService
  ) {}

  /**
   * Renvoie la liste des cruved object liés à Monitorings et de l'utilisateur connecté
   */
  getCruvedMonitoring() {
    return this._cacheService.request('get', `cruved_object`);
  }

  /** Modules */

  /**
   * Renvoie la liste des modules
   */
  getModules(): Array<any> {
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
  urlMonitoring(apiType, moduleCode, objectType, id = null) {
    let url: string;
    const params = [];
    if (objectType.includes('module')) {
      url = moduleCode ? `${apiType}/${moduleCode}/${objectType}` : `${apiType}/module`;
    } else {
      url = id
        ? `${apiType}/${moduleCode}/${objectType}/${id}`
        : `${apiType}/${moduleCode}/${objectType}`;
    }

    return url;
  }

  paramsMonitoring(objectType, queryParams = {}) {
    if (objectType.includes('module')) {
      queryParams['field_name'] = 'module_code';
    }
    return queryParams;
  }

  /**
   * Renvoie un objet pour un module, un type d'objet et un identifiant donnés
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  getObject(moduleCode, objectType, id = null, depth = null) {
    const url = this.urlMonitoring('object', moduleCode, objectType, id);
    const queryParams = this.paramsMonitoring(objectType, { depth });
    return this._cacheService.request('get', url, { queryParams });
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
    return this._cacheService.request('patch', url, { postData });
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
    return this._cacheService.request('post', url, { postData });
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

  /** breadcrumbs */
  /**
   * Renvoie le fil d'ariane d'un object
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   */
  getBreadcrumbs(moduleCode, objectType, id, queryParams) {
    const url = this.urlMonitoring('breadcrumbs', moduleCode, objectType, id);
    return this._cacheService.request('get', url, { queryParams });
  }

  /** Mise à jour de toute la synthèse du module
   * (peut prendre du temps)
   */
  updateSynthese(moduleCode) {
    const url = `synthese/${moduleCode}`;
    return this._cacheService.request('post', url);
  }

  /**
   * Export csv
   *
   *  moduleCode : code du module
   *  method : nom de l'export
   **/

  getExportCsv(moduleCode: string, method: string, queryParams: {}) {
    const url = `exports/csv/${moduleCode}/${method}`;
    const params = {
      postData: {},
      queryParams: queryParams,
    };

    this._cacheService.requestExport('get', url, params);
  }

  /**
   * Export pdf
   *
   * template :  nom du fichier de template pour l'export pdf (.html)
   * map_image : image de la carte leaflet
   *
   **/
  postPdfExport(module_code, object_type, id, template, map_image, extra_data = {}) {
    const url = `exports/pdf/${module_code}/${object_type}/${id}`;
    return this._cacheService.requestExportCreatedPdf('post', url, {
      postData: {
        map: map_image,
        template,
        extra_data,
      },
    });
  }
}
