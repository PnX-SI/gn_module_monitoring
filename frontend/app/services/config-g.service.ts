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
  moduleCode() {
    return this._moduleCode;
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
        this._moduleCode = moduleCode;
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

  getDataTableConfig(objectType: string): Object {
    // TODO ??? Pour le moment dans monitoring-geom-component.ts

    const configObject = this._config[objectType];
    let dataTableConfig = {};
    // Si pas de config, on retourne un objet vide
    if (!configObject) {
      return {};
    }
    return dataTableConfig;
  }

  /**
   * Converti une chaine de caractère en une fonction JS
   *
   * @param s_in - chaine de caractère à convertir en fonction JS
   * @returns La fonction JS correspondante à la chaine de caractère
   */
  toFunction(s_in: string | string[]): ((...args: any[]) => any) | null {
    let s = Array.isArray(s_in) ? s_in.join('\n') : s_in;

    // Vérifie que la chaine de caractère est une string
    if (!(typeof s == 'string')) {
      return null;
    }

    // Vérifie que la chaine de caractère contient des caractères spéciaux
    // qui permettent de définir une fonction JavaScript
    const tests = ['(', ')', '{', '}', '=>'];

    if (!tests.every((test) => s.includes(test))) {
      return null;
    }

    let func;

    try {
      // Essaye de parser la chaine de caractère en fonction JS
      func = eval(s);
    } catch (error) {
      // Affiche un message d'erreur si la fonction ne peut pas être définie
      console.error(`Erreur dans la définition de la fonction ${error} ${s}`);
    }

    return func;
  }

  schema(objectType: string): Object {
    const configObject = this._config[objectType];
    // Si pas de config, on retourne un objet vide
    if (!configObject) {
      return {};
    }

    // gerer quand les paramètres ont un fonction comme valeur
    for (const keyDef of Object.keys(configObject['fields'])) {
      const formDef = configObject['fields'][keyDef];
      for (const keyParam of Object.keys(formDef)) {
        const func = this.toFunction(formDef[keyParam]);
        if (func) {
          formDef[keyParam] = func;
          configObject['fields'][keyDef][keyParam] = func;
        }
      }
    }
    return configObject['fields'];
  }

  fieldLabels(schema): Object {
    const fieldLabels = {};
    for (const key of Object.keys(schema)) {
      fieldLabels[key] = schema[key]['attribut_label'];
    }
    return fieldLabels;
  }

  fieldDefinitions(schema) {
    const fieldDefinitions = {};
    for (const key of Object.keys(schema)) {
      fieldDefinitions[key] = schema[key]['definition'];
    }
    return fieldDefinitions;
  }
}
