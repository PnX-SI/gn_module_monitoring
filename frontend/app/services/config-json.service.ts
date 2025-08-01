import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';
import { Observable, forkJoin, of } from 'rxjs';
import { ConfigService } from './config.service';
import { Utils } from '../utils/utils';
import { DataUtilsService } from './data-utils.service';
import { catchError, concatMap } from 'rxjs/operators';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';

@Injectable()
export class ConfigJsonService extends ConfigService {
  constructor(
    _http: HttpClient,
    _moduleService: ModuleService,
    appConfig: GnConfigService,
    private _dataUtilsService: DataUtilsService
  ) {
    super(_http, _moduleService, appConfig);
  }

  /** Configuration */

  init(moduleCode: string) {
    if (this._config && this._config[moduleCode]) {
      return of(true);
    } else {
      return this.loadConfig(moduleCode);
    }
  }

  /** Backend Module Url */
  backendModuleUrl() {
    // Test if api endpoint have a final slash
    let api_url = this.appConfig.API_ENDPOINT;
    if (api_url.substring(api_url.length - 1, 1) !== '/') {
      api_url = api_url + '/';
    }
    return `${api_url}${this._moduleService.currentModule.module_path}`;
  }
}
