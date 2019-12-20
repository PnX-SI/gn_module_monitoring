import { Injectable } from "@angular/core";
import { HttpClient, HttpEvent, HttpParams, HttpRequest } from "@angular/common/http";

import { Observable } from "rxjs/Observable";
import "rxjs/add/observable/forkJoin";

import { ConfigService } from "../../services/config.service";

/**
 *  Service pour gérer les upload de fichiers 
 * */
@Injectable()
export class UploadService {

  constructor(
      private _http: HttpClient,
      private _config: ConfigService
      ) {}

  uploadFile(file: File, media): Observable<HttpEvent<any>> {
    let formData = new FormData();
    let postData= media;
    for (let p in postData) {
      if (postData[p]) {
        formData.append(p, postData[p])
      }
    }

    formData.append('file', file);
    let params = new HttpParams();
    const options = {
      params: params,
      reportProgress: true,
      responseType: 'json '
    };

    let url = `${this._config.backendUrl()}/gn_commons/media`;
    
    const req = new HttpRequest('POST', url, formData, options);
    return this._http.request(req);
  }
}
