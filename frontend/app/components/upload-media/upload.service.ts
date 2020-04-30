import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpParams, HttpRequest } from '@angular/common/http';

import { Observable } from '@librairies/rxjs';

import { ConfigService } from '../../services/config.service';

/**
 *  Service pour gérer les upload de fichiers
 * */
@Injectable()
export class UploadService {

  constructor(
      private _http: HttpClient,
      private _config: ConfigService
      ) {}


  deleteMedia(idMedia) {
    const req = new HttpRequest('DELETE', `${this._config.backendUrl()}/gn_commons/media/${idMedia}`);
    return this._http.request(req);
  }

  uploadFile(file: File, media): Observable<HttpEvent<any>> {
    const formData = new FormData();
    const postData = media;
    for (const p in postData) {
      if (postData[p]) {
        formData.append(p, postData[p]);
      }
    }

    formData.append('file', file);
    const params = new HttpParams();
    // const options = {
    //   params: params,
    //   reportProgress: true,
    //   responseType: 'json '
    // };

    const url = `${this._config.backendUrl()}/gn_commons/media`;

    const req = new HttpRequest('POST', url, formData);
    return this._http.request(req);
  }
}
