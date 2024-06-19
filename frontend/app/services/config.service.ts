import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ModuleService } from '@geonature/services/module.service';
import { of } from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';

@Injectable()
export class ConfigService {
  protected _config;

  constructor(
    protected _http: HttpClient,
    protected _moduleService: ModuleService,
    public appConfig: GnConfigService
  ) {}

  /** Configuration */

  init(moduleCode: string | null = null) {
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

  loadConfigSpecificConfig(obj) {
    const urlConfig = `${this.backendModuleUrl()}/sites/${obj.id}/types`;
    return this._http.get<any>(urlConfig);
  }

  /** Backend Url et static dir ??*/
  backendUrl() {
    return `${this.appConfig.API_ENDPOINT}`;
  }

  urlApplication() {
    return `${this.appConfig.URL_APPLICATION}`;
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

  descriptionModule() {
    return this.appConfig.MONITORINGS.DESCRIPTION_MODULE;
  }
  titleModule() {
    return this.appConfig.MONITORINGS.TITLE_MODULE;
  }

  codeListObservers() {
    return this.appConfig.MONITORINGS.CODE_OBSERVERS_LIST;
  }
  /** Frontend Module Monitoring Url */
  frontendModuleMonitoringUrl() {
    return this._moduleService.currentModule.module_path;
  }

  moduleCruved(module_code) {
    const permObjectDict = this.appConfig.MONITORINGS.PERMISSION_LEVEL;
    const module = this._moduleService.getModule(module_code);

    const moduleCruved = {};
    for (const [objectCode, permObjectCode] of Object.entries(permObjectDict)) {
      moduleCruved[objectCode] =
        module.objects.find((o) => o.code_object == permObjectDict[objectCode])?.cruved ||
        module.cruved;
    }
    return moduleCruved;
  }

  moduleMonitoringCode() {
    return this.appConfig.MONITORINGS.MODULE_CODE;
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
    moduleCode = moduleCode || 'MONITORINGS';
    const configObject = this._config[moduleCode][objectType];
    // gerer quand les paramètres ont un fonction comme valeur
    if (configObject) {
      for (const typeSchema of ['generic', 'specific']) {
        for (const keyDef of Object.keys(configObject[typeSchema])) {
          const formDef = configObject[typeSchema][keyDef];
          for (const keyParam of Object.keys(formDef)) {
            const func = this.toFunction(formDef[keyParam]);
            const [varNameConfig, varValueConfig] = this.extractVariable(
              keyParam,
              formDef[keyParam]
            );
            if (func) {
              formDef[keyParam] = func;
            }
            if (varValueConfig) {
              configObject[typeSchema][keyDef][keyParam] = formDef[keyParam].replace(
                varNameConfig,
                varValueConfig
              );
            }
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

  addSpecificConfig(types_site) {
    let schemaSpecificType = {};
    let schemaTypeMerged = {};
    let keyHtmlToPop = '';
    for (let type_site of types_site) {
      if (type_site['config'] && 'specific' in type_site['config']) {
        for (const prop in type_site['config']['specific']) {
          if (
            'type_widget' in type_site['config']['specific'][prop] &&
            type_site['config']['specific'][prop]['type_widget'] == 'html'
          ) {
            keyHtmlToPop = prop;
          }
        }
        const { [keyHtmlToPop]: _, ...specificObjWithoutHtml } = type_site['config']['specific'];
        Object.assign(schemaSpecificType, specificObjWithoutHtml);
        Object.assign(schemaTypeMerged, type_site['config']);
      }
    }

    const fieldNames = schemaTypeMerged['display_properties'];
    const fieldNamesList = schemaTypeMerged['display_list'];
    const fieldLabels = this.fieldLabels(schemaSpecificType);
    const fieldDefinitions = this.fieldDefinitions(schemaSpecificType);
    const obj = {};
    obj['template_specific'] = {};
    obj['template_specific']['fieldNames'] = fieldNames;
    obj['template_specific']['fieldNamesList'] = fieldNamesList;
    obj['template_specific']['schema'] = schemaSpecificType;
    obj['template_specific']['fieldLabels'] = fieldLabels;
    obj['template_specific']['fieldDefinitions'] = fieldDefinitions;
    obj['template_specific']['fieldNamesList'] = fieldNamesList;

    return obj['template_specific'];
  }

  fieldLabels(schema) {
    const fieldLabels = {};
    for (const key of Object.keys(schema)) {
      fieldLabels[key] = schema[key]['attribut_label'];
    }
    return fieldLabels;
  }

  fieldNames(moduleCode, objectType, typeDisplay = '', confObject = {}) {
    console.log('HOOOO');

    if (['display_properties', 'display_list'].includes(typeDisplay)) {
      if (Object.keys(confObject).length > 0) {
        console.log('LA?????');
        console.log(confObject);
        console.log(typeDisplay);

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

  extractVariable(keyParam: string, KeyValue: string) {
    let varToReplace;
    let keyVarToChange;
    let keyParamsToIgnore: string[] = ['api'];
    for (const [varConfigName, varCOnfigValue] of Object.entries(this.appConfig.MONITORINGS)) {
      const isVariableToChange =
        !keyParamsToIgnore.includes(keyParam) &&
        typeof KeyValue === 'string' &&
        KeyValue.includes(varConfigName);
      varToReplace = isVariableToChange ? varCOnfigValue : null;
      keyVarToChange = isVariableToChange ? varConfigName : null;
      if (isVariableToChange) {
        break;
      }
    }
    return [keyVarToChange, varToReplace];
  }
}
