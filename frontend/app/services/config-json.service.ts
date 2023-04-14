import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';
import { AppConfig } from '@geonature_config/app.config';
import { of } from 'rxjs';
import { ConfigService } from './config.service';



@Injectable()
export class ConfigJsonService extends ConfigService {

  constructor(_http: HttpClient, _moduleService: ModuleService) {
    super(_http, _moduleService)
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
    let api_url = AppConfig.API_ENDPOINT;
    if (api_url.substring(api_url.length - 1, 1) !== '/') {
      api_url = api_url + '/';
    }
    return `${api_url}${this._moduleService.currentModule.module_path}`;
  }

  fieldLabels(schema) {
    const fieldLabels = {};
    for (const key of Object.keys(schema)) {
      fieldLabels[key] = schema[key]['attribut_label'];
    }
    return fieldLabels;
  }

  fieldNames(moduleCode, objectType, typeDisplay = '') {
    if (['display_properties', 'display_list'].includes(typeDisplay)) {
      return this.configModuleObjectParam(moduleCode, objectType, typeDisplay);
    }
    if (typeDisplay === 'schema') {
      return Object.keys(this.schema(moduleCode, objectType));
    }
  }

  fieldDefinitions(schema) {
    const fieldDefinitions = {};
    for (const key of Object.keys(schema)) {
      fieldDefinitions[key] = schema[key]['definition'];
    }
    return fieldDefinitions;
  }
}
