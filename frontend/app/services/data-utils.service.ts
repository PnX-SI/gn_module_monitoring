import { Injectable } from '@angular/core';

import { Observable, forkJoin, of } from 'rxjs';
import { concatMap, mergeMap, map } from 'rxjs/operators';

import { Utils } from './../utils/utils';

import { CacheService } from './cache.service';
import { ConfigService } from './config.service';
import { DataFormService } from '@geonature_common/form/data-form.service';

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class DataUtilsService {
  constructor(
    private _cacheService: CacheService,
    private _configService: ConfigService,
    private _commonsDataFormService: DataFormService
  ) {}

  /** Util (Nomenclature, User, Taxonomy) */

  /**
   * Renvoie un champ d'un objet de type nomenclare, taxonomy ou utilisateur à partir de son id
   *
   * @param typeUtil le type de l'objet (nomenclature, taxonomy, utilisateur, ...)
   * @param id identifiant de l'objet
   * @param fieldName nom du champ requis, renvoie l'objet entier si 'all'
   */
  getUtil(typeUtil: string, id, fieldName: string, idFieldName: string = null) {
    if (Array.isArray(id)) {
      return this.getUtils(typeUtil, id, fieldName, idFieldName);
    }

    // url relative
    var urlRelative = `util/${typeUtil}/${id}`;

    if (idFieldName) {
      urlRelative += `?id_field_name=${idFieldName}`;
    }

    // parametre pour le stockage dans le cache
    const sCachePaths = `util|${typeUtil}|${id}`;
    // récupération dans le cache ou requête si besoin
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths).pipe(
      mergeMap((value) => {
        let out;
        if (fieldName === 'all') {
          out = value;
        } else if (fieldName.split(',').length >= 2) {
          // plusieurs champs par ex 'nom_vern,lb_nom' si nom_vern null alors lb_nom
          for (const fieldNameInter of fieldName.split(',')) {
            if (value[fieldNameInter]) {
              out = value[fieldNameInter];
              break;
            }
          }
        } else {
          out = value[fieldName];
        }
        return of(out);
      })
    );
  }

  /**
   * Renvoie tableau de champs d'objets de type nomenclare, taxonomy ou utilisateur
   *
   * @param typeUtilObject le type de l'objet (nomenclature, taxonomy, utilisateur, ...)
   * @param ids tableau d'identifiant des objets
   * @param fieldName nom du champ requis, renvoie l'objet entier si 'all'
   */
  getUtils(typeUtilObject, ids, fieldName, idFieldName = null) {
    if (!ids.length) {
      return of(null);
    }
    const observables = [];
    // applique getUtil pour chaque id de ids
    for (const id of ids) {
      observables.push(this.getUtil(typeUtilObject, id, fieldName, idFieldName));
    }
    // renvoie un forkJoin du tableau d'observables
    return forkJoin(observables).pipe(
      concatMap((res) => {
        return of(res.join(', '));
      })
    );
  }

  initModuleNomenclatures(moduleCode: string): Observable<any> {
    /**
     * Récupération et mise en cache de l'ensemble des nomenclatures utilisées dans le module
     *
     * @param moduleCode the module code
     * @returns an Observable that completes when the nomenclatures are stored in cache
     */

    // Récupération des types de nomenclatures utilisées dans le module
    const nomenclatureTypes =
      this._configService.configModuleObject(moduleCode, 'data')['nomenclature'] || [];
    // Récupération des nomenclatures mise en forme et stockage en cache
    return this._commonsDataFormService.getNomenclatures(nomenclatureTypes).pipe(
      map((nomenclatures) => {
        for (const key of Object.keys(nomenclatures)) {
          for (const nomenclature of nomenclatures[key].values || []) {
            let nomenclatureToStore = nomenclature;
            nomenclatureToStore['code_type'] = nomenclatures[key].mnemonique;
            this._cacheService.setCacheValue(
              `util|nomenclature|${nomenclature['id_nomenclature']}`,
              nomenclature
            );
          }
        }
      })
    );
  }

  /** Renvoie une nomenclature à partir de son type et son code */
  getNomenclature(typeNomenclature, codeNomenclature) {
    const urlRelative = `util/nomenclature/${typeNomenclature}/${codeNomenclature}`;
    const sCachePaths = `util|nomenclature|${typeNomenclature}|${codeNomenclature}`;
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths);
  }

  getDataUtil(key) {
    return (this._cacheService['_cache']['util'] || [])[key];
  }

  getUsersByCodeList(codeMenu) {
    const urlRelative = `users/menu_from_code/${codeMenu}`;
    const sCachePaths = `users|menu_from_code|${codeMenu}`;
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths);
  }
}
