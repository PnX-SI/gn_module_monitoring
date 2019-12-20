import { Injectable } from "@angular/core";

import { Observable } from "rxjs/Observable";
import "rxjs/add/observable/forkJoin";

import { Utils } from "./../utils/utils";

import { CacheService } from "./cache.service";
import { ConfigService } from "./config.service";
import { DataFormService } from "@geonature_commons/form/data-form.service"


/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class DataUtilsService {

  constructor(
    private _cacheService: CacheService,
    private _configService: ConfigService,
    private _commonsDataFromService: DataFormService
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
    // si id est un tableau on renvoie getUtils    
    if (Array.isArray(id)) {
      return this.getUtils(typeUtil, id, fieldName);
    }

    if(typeUtil == 'nomenclature' && Utils.isObject(id) && id.code_nomenclature_type && id.cd_nomenclature) {
      return this.getNomenclature(id.code_nomenclature_type, id.cd_nomenclature, fieldName)
    }

    // url relative
    let urlRelative = `util/${typeUtil}/${id}?field_name=${fieldName}`;
    // parametre pour le stockage dans le cache
    let sCachePaths = `util|${typeUtil}|${id}`;
    // récupération dans le cache ou requête si besoin
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths, fieldName);
  }

  /**
   * Renvoie tableau de champs d'objets de type nomenclare, taxonomy ou utilisateur
   * 
   * @param typeUtilObject le type de l'objet (nomenclature, taxonomy, utilisateur, ...)
   * @param ids tableau d'identifiant des objets
   * @param fieldName nom du champ requis, renvoie l'objet entier si 'all' 
   */
  getUtils(typeUtilObject, ids, fieldName) {
    let observables = [];
    // applique getUtil pour chaque id de ids
    for (let id of ids) {
      observables.push(this.getUtil(typeUtilObject, id, fieldName));
    }
    // renvoie un forkJoin du tableau d'observables
    return Observable.forkJoin(observables);
  }

  /** Renvoie une nomenclature à partir de son type et son code */
  getNomenclature(typeNomenclature, codeNomenclature, fieldName) {
    let urlRelative = `util/nomenclature/${typeNomenclature}/${codeNomenclature}?field_name=${fieldName}`;
    let sCachePaths =  `util|nomenclature|${typeNomenclature}|${codeNomenclature}`;
    return this._cacheService.cache_or_request('get', urlRelative, sCachePaths, fieldName);
  }

  /** Récupère les données qui seront utiles pour le module */
  getInitData(modulePath): Observable<any> {
    /** Les données à récupérer sont spécifiées dans la config du module 
     * config/<module_path>/data_config.json et 
     * config/<module_path>/custom_config.json
    */

    const configData = this._configService.configData(modulePath);

    let nomenclatureRequest = null;
    // Taxonomie (liste ou ensemble de )

    // User
    return Observable.of(true)
  }

}
