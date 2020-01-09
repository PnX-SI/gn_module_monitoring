import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

import { Observable, of } from "rxjs";
import "rxjs/add/observable/forkJoin";

import { ConfigService } from "./config.service";

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class CacheService {

  private _cache = {};

  constructor(private _http: HttpClient, private _config: ConfigService) { }

  /** http request */

  /**
   * requête générique
   * 
   * @param requestType get, post, patch ou delete
   * @param urlRelative url relative de la route
   * @param data post data (optionnel)
   */
  request(requestType: string, urlRelative: string, data = {}) {
    // verification de requestType
    if (!['get', 'post', 'patch', 'delete'].includes(requestType)) {
      return of(null);
    }
    // requete
    return this._http[requestType]<any>(this._config.backendModuleUrl() + '/' + urlRelative, data);
  }


  /** Cache 
    * Essaye de recupérer un donnée depuis le cache
    * 
    /**
     * @param sCachePaths chaine de caractères tableau qui permet de parcourir le dictionnaire _cache
     * 
  
     */
  getFromCache(sCachePaths: string) {
    let cachePaths = sCachePaths.split('|');

    // parcours du dictionnaire _cache
    let current = this._cache;
    for (let path of cachePaths) {
      if (!current[path]) {
        return undefined;
      }
      current = current[path];
    }
    return current;
  }


  /**
     * Renseigne une donnée dans le cache
     * 
     * @param sCachePaths chaine de caractères tableau qui permet de parcourir le dictionnaire _cache
     * @param value valeur a assigner au cache
     * 
     * par exemple on souhaite renseigner le noms francais du taxon 591558
     * _cache
     * ____ 'utils'
     * ________ 'taxonomy'

     * la comande sera :
     *  setCacheValue('utils|taxonomy|591558', 'nom_francais')
     */
  setCacheValue(sCachePaths: string, value: any) {
    let cachePaths = sCachePaths.split('|');

    // parcours du cache
    let current = this._cache;
    for (let path of cachePaths) {
      current = current[path] = current[path] ? current[path] : {};
    }

    for( let key in value) {
      current[key] = value[key];
    }

  }

  /**
   * recupere le resultat d'une requete en cache
   * effectue la requete si besoin et stocke le resultat en cache
   * renvoie un observable
   * 
   * @param value valeur a assigner au cache
   * @param requestType get, post, patch ou delete
   * @param urlRelative url relative de la route
   * @param sCachePaths chaine de caractères tableau qui permet de parcourir le dictionnaire _cache
   */
  cache_or_request(requestType: string, urlRelative: string, sCachePaths: string) {
    // on renvoie un observable
    return new Observable(observer => {

      // recuperation depuis le cache
      let valueCache = this.getFromCache(sCachePaths);
      if (valueCache != undefined) {
        // envoie de la valeur à l'observer
        observer.next(valueCache);
        return observer.complete();
      }

      let request = this.request(requestType, urlRelative);

      // si la donnée n'est pas dans le cache on effectue la requête
      request.subscribe(
        value => {
          // stockage de la donnée en cache
          this.setCacheValue(sCachePaths, value);
          // envoie de la valeur à l'observer
          observer.next(value);
          return observer.complete();
        }
      );
    });
  }

  cache() {
    return this._cache;
  }

}
