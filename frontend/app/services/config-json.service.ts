import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ModuleService } from '@geonature/services/module.service';
import { AppConfig } from '@geonature_config/app.config';
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

  fieldNames(moduleCode, objectType, typeDisplay = '', confObject = {}) {
    if (['display_properties', 'display_list'].includes(typeDisplay)) {
      if (Object.keys(confObject).length > 0) {
        return confObject[typeDisplay];
      }
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

  //NEW - récup setResolvedProperties from monitoring-object-base.ts

  resolveProperty(elem, val, moduleCode): Observable<any> {
    if (elem.type_widget === 'date' || (elem.type_util === 'date' && val)) {
      val = Utils.formatDate(val);
    }
    const fieldName = this._config[moduleCode].default_display_field_names[elem.type_util];
    if (val && fieldName && elem.type_widget) {
      return this._dataUtilsService.getUtil(elem.type_util, val, fieldName, elem.value_field_name);
    }
    return of(val);
    // return val
  }

  // TODO: Cette fonction permet de traduire l'affichage de certains champs dans propriété ou le formulaire
  // lorsqu'on a des valeurs à récupérer depuis le backend via les config json.
  // Du coup , penser à résoudre le problèmes des champs dans le fichier de config.json
  // en modifiant le fichier : /gn_module_monitoring/backend/gn_module_monitoring/config/repositories.py
  //  Function : get_config
  setResolvedProperties(obj): any {
    const observables = {};
    if (obj.resolvedProperties == undefined) {
      obj.resolvedProperties = {};
    }

    const schema = this.schema(obj.moduleCode, obj.objectType);
    for (const attribut_name of Object.keys(schema)) {
      observables[attribut_name] = this.resolveProperty(
        schema[attribut_name],
        obj.properties[attribut_name],
        obj.moduleCode
      );
    }
    forkJoin(observables).pipe(
      concatMap((resolvedProperties) => {
        for (const attribut_name of Object.keys(resolvedProperties)) {
          obj.resolvedProperties[attribut_name] = resolvedProperties[attribut_name];
        }
        return obj.resolvedProperties;
      })
    );
  }

  // TODO: essaye d'utiliser cette méthode pour obtenir les propriétés "resolved"
  // setResolvedPropertiesForItem(obj, item = null): any {
  //   const observables = {};

  //   const schema = this.schema(obj.moduleCode, obj.objectType);
  //   for (const attribut_name of Object.keys(schema)) {
  //     observables[attribut_name] = this.resolveProperty(
  //       schema[attribut_name],
  //       item[attribut_name],
  //       obj.moduleCode
  //     );
  //   }
  //   return forkJoin(observables).pipe(
  //     concatMap((resolvedProperties) => {
  //       const resolvedPropertiesItem: any = {};
  //       for (const attribut_name of Object.keys(resolvedProperties)) {
  //         resolvedPropertiesItem[attribut_name] = resolvedProperties[attribut_name];
  //       }
  //       return resolvedPropertiesItem;
  //     }),
  //     catchError((err) => {
  //       console.log(err);
  //       return of(null);
  //     })
  //   );
  // }
}
