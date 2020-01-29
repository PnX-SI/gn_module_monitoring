import { Injectable } from '@angular/core';

import { Observable, forkJoin, of } from '@librairies/rxjs';
import { concatMap , mergeMap } from '@librairies/rxjs/operators';

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
  ) { }

  /** Util (Nomenclature, User, Taxonomy) */

  /**
   * Renvoie un champ d'un objet de type nomenclare, taxonomy ou utilisateur à partir de son id
   *
   * @param typeUtil le type de l'objet (nomenclature, taxonomy, utilisateur, ...)
   * @param id identifiant de l'objet
   * @param fieldName nom du champ requis, renvoie l'objet entier si 'all'
   */
  getUtil(typeUtil: string, id, fieldName: string) {

    if (Array.isArray(id)) {
      return this.getUtils(typeUtil, id, fieldName);
    }

    // url relative
    const urlRelative = `util/${typeUtil}/${id}`;
    // parametre pour le stockage dans le cache
    const sCachePaths = `util|${typeUtil}|${id}`;
    // récupération dans le cache ou requête si besoin
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths)
      .pipe(
        mergeMap(
          value => {
            const out = fieldName === 'all' ? value : value[fieldName];
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
  getUtils(typeUtilObject, ids, fieldName) {
    if (!ids.length) {
      return of(null);
    }
    const observables = [];
    // applique getUtil pour chaque id de ids
    for (const id of ids) {
      observables.push(this.getUtil(typeUtilObject, id, fieldName));
    }
    // renvoie un forkJoin du tableau d'observables
    return forkJoin(observables)
      .pipe(
        concatMap(res => {
          return of(res.join(' ,'));
        })
      );
  }


  /** Renvoie une nomenclature à partir de son type et son code */
  getNomenclature(typeNomenclature, codeNomenclature) {
    const urlRelative = `util/nomenclature/${typeNomenclature}/${codeNomenclature}`;
    const sCachePaths = `util|nomenclature|${typeNomenclature}|${codeNomenclature}`;
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths);
  }

  /** Récupère les données qui seront utiles pour le module */
  getInitData(modulePath): Observable<any> {
    /** Les données à récupérer sont spécifiées dans la config du module
     * config/<module_path>/data_config.json et
     * config/<module_path>/custom_config.json
    */

    const cache = this._cacheService.cache();
    // test si la fonction a déjà été appelée
    if (cache[modulePath] && cache[modulePath]['init_data']) {
      return of(true);
    }

    const observables = {};
    const configData = this._configService.configData(modulePath);

    const nomenclatureRequest = this._commonsDataFormService.getNomenclatures(configData['nomenclature']);
    observables['nomenclature'] = nomenclatureRequest;

    // Taxonomie (liste ou ensemble de )
    const taxonomyRequests = [];
    if (configData.taxonomy && configData.taxonomy.cd_noms) {
      for (const cd_nom of configData.taxonomy.cd_noms) {
        taxonomyRequests.push(this._commonsDataFormService.getTaxonInfo(cd_nom));
      }
    }
    if (taxonomyRequests.length) {
      observables['taxonomy'] = forkJoin(taxonomyRequests);
    }

    const userRequests = [];
    for (const codeList of configData['user']) {
      userRequests.push(this._commonsDataFormService.getObserversFromCode(codeList));
    }
    if (userRequests.length) {
      observables['user'] = forkJoin(userRequests);
    }

    return forkJoin(observables)
      .pipe(
        concatMap((data) => {
          // mise en cache

          const nomenclatures = data['nomenclature'] as Array<any>;
          if (nomenclatures) {
            for (const nomenclature_type of nomenclatures ) {
              for (const nomenclature of nomenclature_type.values) {
                this._cacheService.setCacheValue(`util|nomenclature|${nomenclature['id_nomenclature']}`, nomenclature);
              }
            }
          }

          const userLists = data['user'];
          if (userLists) {
            for (const userList of userLists as Array<any>) {
              for (const user of userList) {
                this._cacheService.setCacheValue(`util|user|${user['id_role']}`, user);
              }
            }
          }

          const taxonomy = data['taxonomy'] as Array<any>;
          if (taxonomy) {
            for (const taxon of taxonomy) {
              this._cacheService.setCacheValue(`util|taxonomy|${taxon['cd_nom']}`, taxon);
            }
          }

          // pour ne pas appeler la fonction deux fois
          if (!cache[modulePath]) {
            cache[modulePath] = {};
          }
          cache[modulePath]['init_data'] = true;

          return of(true);
        })
      );
  }

}
