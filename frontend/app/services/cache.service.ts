import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

import { Observable } from "rxjs/Observable";
import "rxjs/add/observable/forkJoin";

import { Utils } from "./../utils/utils";
import { ConfigService } from "./config.service";

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class CacheService {

  private _cache = {};
  private _pendingCache = {};

  constructor(private _http: HttpClient, private _config: ConfigService) {}

  /** http request */

  /**
   * requête générique
   * 
   * @param requestType get, post, patch ou delete
   * @param urlRelative url relative de la route
   * @param data post data (optionnel)
   */
  request(requestType: string, urlRelative: string, data={}) {
    // verification de requestType
    if (!['get', 'post', 'patch', 'delete'].includes(requestType)) {
      return Observable.of(null);
    }
    // console.log('REQUEST', urlRelative)
    // requete
    return this._http[requestType]<any>(this._config.backendModuleUrl() + '/' + urlRelative, data);
  }
  

/** Cache 
  * Essaye de recupérer un donnée depuis le cache
  * 
  /**
   * @param sCachePaths chaine de caractères tableau qui permet de parcourir le dictionnaire _cache
   * @param fieldName le nom du champ requis, si 'all' on renvoie l'objet entier
   * 
   * par exemple on souhaite connaitre le noms francais du taxon 591558
   * _cache : 'utils' : 'taxonomy' : '591558' : 'nom_francais' : 'Pieuvre mimétique'

   * la comande sera :
   *  getFromCache('utils|taxonomy|591558', 'nom_francais')
   */
  getFromCache(cache, sCachePaths: string, fieldName: string) {
    let out;
    let cachePaths = sCachePaths.split('|');

    // parcours du dictionnaire _cache
    let current = cache;
    for (let path of cachePaths) {
      if (!current[path]) {
        return out;
      }
      current = current[path];
    }

    // test si l'objet possède le parametre fieldName 
    if (fieldName in current) {
      // si fieldName vaut 'all' l'objet entier est renvoyé
      // sinon la valeur du champ est revoyé
      if (fieldName == 'all') {
        out = Utils.copy(current);
        delete out['all'];
      } else {
        out = current[fieldName];
      }
    }

    return out;
  }


  /**
     * Renseigne une donnée dans le cache
     * 
     * @param sCachePaths chaine de caractères tableau qui permet de parcourir le dictionnaire _cache
     * @param value valeur a assigner au cache
     * @param fieldName le nom du champ requis, si 'all' on renvoie l'objet entier
     * 
     * par exemple on souhaite renseigner le noms francais du taxon 591558
     * _cache
     * ____ 'utils'
     * ________ 'taxonomy'

     * la comande sera :
     *  setCacheValue('utils|taxonomy|591558', 'nom_francais')
     */
  setCacheValue(cache, sCachePaths: string, fieldName: string, value: any) {
    let cachePaths = sCachePaths.split('|');

    // parcours du cache
    let current = cache;
    for (let path of cachePaths) {
      current = current[path] = current[path] ? current[path] : {};
    }

    if (fieldName == 'all') {
      // si field name = 'all' on reseigne l'objet entier
      current[fieldName] = value;
      current['all'] = true;
    } else {
      // sinon on renseigne seulement le champs
      current[fieldName] = value;
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
   * @param fieldName le nom du champ requis, si 'all' on renvoie l'objet entier
   */
  cache_or_request(requestType: string, urlRelative: string, sCachePaths: string, fieldName: string) {
    // on renvoie un observable
    return new Observable(observer => {

      // recuperation depuis le cache
      let valueCache = this.getFromCache(this._cache, sCachePaths, fieldName);
      if (valueCache != undefined) {
        // console.log('cache_or_request CACHE', urlRelative);
        // envoie de la valeur à l'observer
        observer.next(valueCache);
        return observer.complete();
      }

      // recuperation depuis le pending cache (si requete en cours)
      let pendingCacheRequest = this.getFromCache(this._pendingCache, sCachePaths, fieldName);
      if (pendingCacheRequest != undefined) {
        // console.log('cache_or_request PENDING_CACHE', urlRelative);
        // envoie de la valeur à l'observer
        
        pendingCacheRequest.subscribe((value) => {
          // console.log('cache_or_request PENDING_CACHE DONE', urlRelative);
          observer.next(value);
          return observer.complete();
        });
        return;
      }


      // console.log('cache_or_request REQUEST', urlRelative);
      let request = this.request(requestType, urlRelative);
      this.setCacheValue(this._pendingCache, sCachePaths, fieldName, request);

      // si la donnée n'est pas dans le cache on effectue la requête
      request.subscribe(
        value => {
          // stockage de la donnée en cache
          this.setCacheValue(this._cache, sCachePaths, fieldName, value);
          // console.log('cache_or_request REQUEST DONE', urlRelative);
          // envoie de la valeur à l'observer
          observer.next(value);
          return observer.complete();
        }
      );
    });
  }


}
