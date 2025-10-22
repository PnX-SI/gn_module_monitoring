import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ModuleService } from '@geonature/services/module.service';
import { of, Observable } from 'rxjs';
import { mergeMap, map } from 'rxjs/operators';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';

@Injectable({
  providedIn: 'root', // a changer :/
})
export class ConfigServiceG {
  protected _config: any;
  protected _moduleCode: string | null = null;

  constructor(
    protected _http: HttpClient,
    protected _moduleService: ModuleService,
    public geonatureConfig: GnConfigService
  ) {}

  // Getter  de la config
  config() {
    return this._config;
  }
  /** Configuration */

  init(moduleCode: string | null = null) {
    // a definir ailleurs
    moduleCode = moduleCode || 'generic';
    if (this._moduleCode === moduleCode && this._config) {
      return of(true);
    } else {
      return this.loadConfig(moduleCode);
    }
  }

  loadConfig(moduleCode: string): Observable<boolean> {
    const urlConfig =
      moduleCode === 'generic'
        ? `${this.backendModuleUrl()}/refacto/config`
        : `${this.backendModuleUrl()}/refacto/config/${moduleCode}`;

    return this._http.get<any>(urlConfig).pipe(
      mergeMap((config: any) => {
        this._config = config;
        return of(true);
      })
    );
  }

  /** Backend Module Url */
  backendModuleUrl() {
    // Test if api endpoint have a final slash
    let api_url = this.geonatureConfig.API_ENDPOINT;
    if (api_url.substring(api_url.length - 1, 1) !== '/') {
      api_url = api_url + '/';
    }
    return `${api_url}${this._moduleService.currentModule.module_path}`;
  }
}
