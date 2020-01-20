import { Utils } from './../utils/utils';
// import _ from "lodash";
import { Injectable } from "@angular/core";

import { HttpClient } from "@angular/common/http";
import { AppConfig } from "@geonature_config/app.config";
import { ModuleConfig } from "../module.config";

import { of } from "@librairies/rxjs";
import { mergeMap } from "@librairies/rxjs/operators";

@Injectable()
export class ConfigService {
  private _config;

  constructor(private _http: HttpClient) { }

  /** Configuration */

  init(modulePath = null) {

    // a definir ailleurs

    modulePath = modulePath || 'generic';

    if (this._config && this._config[modulePath]) {
      return of(true);
    } else {
      console.log('config get');
      let urlConfig = modulePath == 'generic' ? `${this.backendModuleUrl()}/config` : `${this.backendModuleUrl()}/config/${modulePath}`
      return this._http.get<any>(urlConfig)
        .pipe(
          mergeMap((config) => {
            this._config = this._config || {};
            this._config[modulePath] = config;
            this._config['frontendParams'] = {
              'bChainInput': false
            }
            return of(true);
          })
        );
    }
  }

  /** Backend Url et static dir ??*/
  backendUrl() {
    return `${AppConfig.API_ENDPOINT}`;
  }

  /** Backend Module Url */
  backendModuleUrl() {
    return `${AppConfig.API_ENDPOINT}/${ModuleConfig.MODULE_URL}`;
  }

  /** Frontend Module Monitoring Url */
  frontendModuleMonitoringUrl() {
    return ModuleConfig.MODULE_URL;
  }

  moduleMonitoringCode() {
    return ModuleConfig.MODULE_CODE;
  }

  /** Config Object Schema */
  schema(modulePath, objectType, typeSchema = "all") {
    modulePath = modulePath || 'generic';
    let schemas = this._config[modulePath].schemas[objectType]
    let generic = schemas.generic;
    let specific = schemas.specific;

    switch (typeSchema) {
      case "all": {
        return generic.concat(specific);
      }
      case "generic": {
        return generic;
      }
      case "specific": {
        return specific;
      }
    }
  }

  getFormDef(modulePath, objectType, key, keyType = "attribut_name", typeSchema = "all") {
    modulePath = modulePath || 'generic';
    return this.schema(modulePath, objectType, typeSchema)
      .find(formDef =>
        formDef[keyType] == key
      );
  }

  /**
   * Renvoie un element de configuration d'un objet pour un module donné
   * 
   * ex: getconfigModuleObjectParam('objects', 'oedic', 'site', 'descrition_field_name') renvoie 'base_site_name'
   */
  configModuleObjectParam(typeConfig: string, modulePath: string, objectType: string, fieldName: string) {
    modulePath = modulePath || 'generic';
    let confObject = this._config[modulePath][typeConfig][objectType];
    return confObject ? confObject[fieldName] : null;
  }

  /** config data : pour initialiser les données Nomenclature, Taxons, Users,... 
   * contient une liste de type de nomenclature, les liste d'utilisateur et une liste de taxon
  */
  configData(modulePath) {
    return this._config[modulePath]['data']
  }

  frontendParams() {
    return this._config.frontendParams;
  }

  setFrontendParams(paramName, paramValue) {
    if (this._config && this._config.frontendParams) {
      this._config.frontendParams[paramName] = paramValue;
    }
  }

  cache() {
    return this._config;
  }


}
