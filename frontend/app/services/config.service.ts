import { MonitoringObjectComponent } from './../components/monitoring-object/monitoring-object.component';
import { Utils } from './../utils/utils';
// import _ from "lodash";
import { Injectable } from '@angular/core';

import { HttpClient } from '@angular/common/http';
import { AppConfig } from '@geonature_config/app.config';
import { ModuleConfig } from '../module.config';
import { ModuleService } from '@geonature/services/module.service';
import { of } from 'rxjs';
import { mergeMap } from 'rxjs/operators';

@Injectable()
export class ConfigService {
  private _config;

  constructor(private _http: HttpClient, private _moduleService: ModuleService) {}

  /** Configuration */

  init(moduleCode = null) {
    // a definir ailleurs

    moduleCode = moduleCode || 'generic';

    if (this._config && this._config[moduleCode]) {
      return of(true);
    } else {
      return this.loadConfig(moduleCode);
    }
  }

  loadConfig(moduleCode) {
    const urlConfig =
      moduleCode === 'generic'
        ? `${this.backendModuleUrl()}/config`
        : `${this.backendModuleUrl()}/config/${moduleCode}`;
    return this._http.get<any>(urlConfig).pipe(
      mergeMap((config) => {
        this._config = this._config || {};
        this._config[moduleCode] = config;
        this._config['frontendParams'] = {
          bChainInput: false,
        };
        return of(true);
      })
    );
  }

  /** Backend Url et static dir ??*/
  backendUrl() {
    return `${AppConfig.API_ENDPOINT}`;
  }

  urlApplication() {
    return `${AppConfig.URL_APPLICATION}`;
  }

  /** Backend Module Url */
  backendModuleUrl() {
    // Test if api endpoint have a final slash
    let api_url = AppConfig.API_ENDPOINT;
    if (api_url.substring(api_url.length - 1, 1) !== '/') {
      api_url = api_url + '/';
    }
    return `${api_url}${this._moduleService.currentModule.module_path}`;
  }

  descriptionModule() {
    return ModuleConfig.DESCRIPTION_MODULE;
  }
  titleModule() {
    return ModuleConfig.TITLE_MODULE;
  }
  /** Frontend Module Monitoring Url */
  frontendModuleMonitoringUrl() {
    return this._moduleService.currentModule.module_path;
  }

  moduleMonitoringCode() {
    return ModuleConfig.MODULE_CODE;
  }

  /**
   * Converti s en function js
   *
   *
   * @param s chaine de caractere
   */
  toFunction(s_in) {
    let s = Array.isArray(s_in) ? s_in.join('\n') : s_in;

    if (!(typeof s == 'string')) {
      return;
    }

    const tests = ['(', ')', '{', '}', '=>'];

    if (!tests.every((test) => s.includes(test))) {
      return;
    }

    let func;

    try {
      func = eval(s);
    } catch (error) {
      console.error(`Erreur dans la définition de la fonction ${error} ${s}`);
    }

    return func;
  }

  /**
   * Pour récupérer la function change qui précise la procédure en cas de changement de valeur du formulaire
   * @param moduleCode
   * @param objectType
   */
  change(moduleCode, objectType) {
    moduleCode = moduleCode || 'generic';

    const configObject = this._config[moduleCode][objectType];
    const change = configObject.change;
    return this.toFunction(change);
  }

  /** Config Object Schema */
  schema(moduleCode, objectType, typeSchema = 'all'): Object {
    moduleCode = moduleCode || 'generic';

    const configObject = this._config[moduleCode][objectType];

    // gerer quand les paramètres ont un fonction comme valeur

    for (const typeSchema of ['generic', 'specific']) {
      for (const keyDef of Object.keys(configObject[typeSchema])) {
        const formDef = configObject[typeSchema][keyDef];
        for (const keyParam of Object.keys(formDef)) {
          const func = this.toFunction(formDef[keyParam]);
          if (func) {
            formDef[keyParam] = func;
          }
        }
      }
    }

    // patch media TODO fix
    if (!configObject) {
      return {};
    }

    switch (typeSchema) {
      case 'all': {
        return { ...configObject.generic, ...configObject.specific };
      }
      case 'generic': {
        return configObject.generic;
      }
      case 'specific': {
        return configObject.specific;
      }
    }
  }

  configModuleObject(moduleCode: string, objectType: string) {
    moduleCode = moduleCode || 'generic';
    return this._config[moduleCode][objectType];
  }

  /**
   * Renvoie un element de configuration d'un objet pour un module donné
   *
   * ex: getconfigModuleObjectParam('objects', 'oedic', 'site', 'descrition_field_name') renvoie 'base_site_name'
   */
  configModuleObjectParam(moduleCode: string, objectType: string, fieldName: string) {
    const confObject = this.configModuleObject(moduleCode, objectType);
    return confObject ? confObject[fieldName] : null;
  }

  /** config data : pour initialiser les données Nomenclature, Taxons, Users,...
   * contient une liste de type de nomenclature, les liste d'utilisateur et une liste de taxon
   */
  configData(moduleCode) {
    return this._config[moduleCode]['data'];
  }

  frontendParams() {
    return this._config.frontendParams;
  }

  setFrontendParams(paramName, paramValue) {
    if (this._config && this._config.frontendParams) {
      this._config.frontendParams[paramName] = paramValue;
    }
  }

  config() {
    return this._config;
  }

  cache() {
    return this._config;
  }
}
