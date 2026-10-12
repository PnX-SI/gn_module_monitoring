import { Observable, of } from 'rxjs';
import { Injectable } from '@angular/core';

import { CacheService } from './cache.service';

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class DataMonitoringObjectService {
  constructor(private _cacheService: CacheService) {}

  /** Modules */

  /**
   * Renvoie la liste des modules
   */
  getModules(): Observable<any> {
    // Utilisé dans modules.component
    return this._cacheService.request('get', `modules`);
  }

  /** Object */
  urlMonitoring(apiType, moduleCode, objectType, id = null) {
    let url: string;
    if (objectType.includes('module')) {
      url = moduleCode ? `${apiType}/${moduleCode}/${objectType}` : `${apiType}/module`;
    } else {
      url = id
        ? `${apiType}/${moduleCode}/${objectType}/${id}`
        : `${apiType}/${moduleCode}/${objectType}`;
    }

    return url;
  }

  /** breadcrumbs */
  /**
   * Renvoie le fil d'ariane d'un object
   *
   * @param moduleCode le champ module_code du module
   * @param objectType le type de l'objet (site, visit, observation, ...)
   * @param id l'identifiant de l'objet
   * @param queryParams paramètre supplémentaire permettant d'indiquer les parents souhaités
   */
  getBreadcrumbs(moduleCode, objectType, id, queryParams) {
    // Utilisé dans object.service
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
   * id_inventor ???
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
