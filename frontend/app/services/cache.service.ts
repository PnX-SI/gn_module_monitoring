import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

import { Observable, of, Subject } from 'rxjs';
import { mergeMap } from 'rxjs/operators';

import { ConfigService } from './config.service';

/**
 *  Ce service référence et execute les requêtes bers le serveur backend
 *  Les requêtes pour les objects de type nomenclature, utilisateurs, taxonomie ,sont mise en cache
 */
@Injectable()
export class CacheService {
  private _cache = {};
  private _pendingCache = {};

  constructor(
    private _http: HttpClient,
    private _config: ConfigService
  ) { }

  /** http request */

  /**
   * requête générique
   *
   * @param requestType get, post, patch ou delete
   * @param urlRelative url relative de la route
   * @param data post data (optionnel)
   */
  request<Return = Observable<any>>(
    requestType: string,
    urlRelative: string,
    { postData = {}, queryParams = {} } = {}
  ): Return {
    // verification de requestType
    if (!['get', 'post', 'patch', 'delete'].includes(requestType)) {
      throw console.error('Request must be get, post, patch or delete');
    }

    const url_params = Object.keys(queryParams).length
      ? '?' +
      Object.keys(queryParams)
        .map((key) =>
          Array.isArray(queryParams[key])
            ? queryParams[key].map((val) => `${key}=${val}`).join('&')
            : `${key}=${queryParams[key]}`
        )
        .join('&')
      : '';
    let url: string;
    if (urlRelative.includes('menu_from_code')) {
      url = this._config.backendUrl() + '/' + urlRelative + url_params;
    } else {
      url = this._config.backendModuleUrl() + '/' + urlRelative + url_params;
    }

    // requete
    return this._http[requestType]<Return>(url, postData);
  }

  /** Cache
    * Essaye de recupérer un donnée depuis le cache
    *
    /**
     * @param sCachePaths chaine de caractères tableau qui permet de parcourir le dictionnaire _cache
     *

     */
  getFromCache(sCachePaths: string, cache = null) {
    cache = cache || this._cache;

    const cachePaths = sCachePaths.split('|');

    // parcours du dictionnaire _cache
    let current = cache;
    for (const path of cachePaths) {
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
  setCacheValue(sCachePaths: string, value: any, cache = null) {
    cache = cache || this._cache;
    const cachePaths = sCachePaths.split('|');

    const key = cachePaths.pop();

    // parcours du cache
    let current = cache;
    for (const path of cachePaths) {
      current = current[path] = current[path] ? current[path] : {};
    }
    current[key] = value;
  }

  removeCacheValue(sCachePaths: string, cache = null) {
    cache = cache || this._cache;

    const cachePaths = sCachePaths.split('|');

    const key = cachePaths.pop();
    // parcours du cache
    let current = cache;
    for (const path of cachePaths) {
      current = current[path] = current[path] ? current[path] : {};
    }
    delete current[key];
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
    return new Observable((observer) => {
      // recuperation depuis le cache
      const valueCache = this.getFromCache(sCachePaths, this._cache);
      if (valueCache !== undefined) {
        // envoie de la valeur à l'observer
        observer.next(valueCache);
        return observer.complete();
      }

      let pendingSubject = this.getFromCache(sCachePaths, this._pendingCache);
      if (pendingSubject === undefined) {
        pendingSubject = new Subject();
        this.setCacheValue(sCachePaths, pendingSubject, this._pendingCache);
        this.request(requestType, urlRelative).subscribe((value) => {
          // stockage de la donnée en cache
          this.setCacheValue(sCachePaths, value, this._cache);

          // envoie de la valeur à l'observer
          pendingSubject.next(value);
          pendingSubject.complete();
          observer.next(value);
          return observer.complete();
        });
      } else {
        pendingSubject.asObservable().subscribe((value) => {
          observer.next(value);
          return observer.complete();
        });
      }
      // si la donnée n'est pas dans le cache on effectue la requête
    });
  }

  cache() {
    return this._cache;
  }

  requestExport(
    requestType: string,
    urlRelative: string,
    { postData = {}, queryParams = {} } = {}
  ) {
    // verification de requestType

    const url_params = Object.keys(queryParams)
      .map((key) =>
        Array.isArray(queryParams[key])
          ? queryParams[key].map((val) => `${key}=${val}`).join('&')
          : `${key}=${queryParams[key]}`
      )
      .join('&');

    const url = this._config.backendModuleUrl() + '/' + urlRelative + '?' + url_params;

    // requete
    window.open(url);
  }

  //add mje: export pdf
  requestExportCreatedPdf(
    requestType: string,
    urlRelative: string,
    { postData = {}, queryParams = {} } = {}
  ) {
    const httpHeaders: HttpHeaders = new HttpHeaders({
      Accept: 'application/pdf',
    });
    const url = this._config.backendModuleUrl() + '/' + urlRelative;

    return this._http[requestType]<any>(url, postData, {
      responseType: 'arraybuffer',
      headers: httpHeaders,
    }).pipe(
      mergeMap((file) => {
        let blob = new Blob([file as BlobPart], {
          type: 'application/pdf',
        });
        let url = window.URL.createObjectURL(blob);
        window.open(url);
        return of(true);
      })
    );
  }
}
