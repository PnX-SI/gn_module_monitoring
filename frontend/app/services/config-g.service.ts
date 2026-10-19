import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ModuleService } from '@geonature/services/module.service';
import { DataFormService } from '@geonature_common/form/data-form.service';
import { of, Observable } from 'rxjs';
import { mergeMap, map } from 'rxjs/operators';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';
import { API_PREFIX } from '../constants/api';
import { CacheService } from './cache.service';

@Injectable({
  providedIn: 'root', // a changer :/
})
export class ConfigServiceG {
  protected _config: any;
  protected _moduleCode: string = 'generic';

  constructor(
    protected _http: HttpClient,
    protected _moduleService: ModuleService,
    public geonatureConfig: GnConfigService,
    private _cacheService: CacheService,
    private _commonsDataFormService: DataFormService
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
    console.log('ConfigServiceG loadConfig for moduleCode : ', moduleCode);

    const baseUrl = this.geonatureConfig.API_ENDPOINT + '/' + moduleCode;
    const urlConfig =
      moduleCode === 'generic'
        ? `${baseUrl}/${API_PREFIX}/config`
        : `${baseUrl}/${API_PREFIX}/${moduleCode}/config`;
    return this._http.get<any>(urlConfig).pipe(
      mergeMap((config: any) => {
        this._config = config;
        // Traiter les champs de la config pour qu'ils soient exploitables
        // par les composants
        // Ex: transformer les chaines de caractères en fonctions JS
        this.processConfig();
        this._moduleCode = moduleCode;
        // Initialisation des nomenclatures du module
        return this.initModuleNomenclatures();
      })
    );
  }

  initModuleNomenclatures(): Observable<any> {
    /**
     * Récupération et mise en cache de l'ensemble des nomenclatures utilisées dans le module
     *
     * @param moduleCode the module code
     * @returns an Observable that completes when the nomenclatures are stored in cache
     */
    // Récupération des types de nomenclatures utilisées dans le module
    const nomenclatureTypes = this._config['data']['nomenclature'] || [];
    // Récupération des nomenclatures mise en forme et stockage en cache
    return this._commonsDataFormService.getNomenclatures(nomenclatureTypes).pipe(
      map((nomenclatures) => {
        for (const key of Object.keys(nomenclatures)) {
          for (const nomenclature of nomenclatures[key].values || []) {
            let nomenclatureToStore = nomenclature;
            nomenclatureToStore['code_type'] = nomenclatures[key].mnemonique;
            this._cacheService.setCacheValue(
              `util|nomenclature|${nomenclature['id_nomenclature']}`,
              nomenclature
            );
          }
        }
      })
    );
  }

  codeListObservers() {
    if (this._config['custom']['CODE_OBSERVERS_LIST']) {
      return this._config['custom']['CODE_OBSERVERS_LIST'];
    }
    return this.geonatureConfig.MONITORINGS.CODE_OBSERVERS_LIST;
  }

  /** Frontend Module Monitoring Url */
  frontendModuleMonitoringUrl() {
    return this._moduleService.currentModule.module_path;
  }

  processConfig() {
    for (const keys of Object.keys(this._config)) {
      if (this._config[keys] && Object.keys(this._config[keys]).includes('fields')) {
        this._config[keys] = this.processFields(keys);
      }
      if (this._config[keys] && Object.keys(this._config[keys]).includes('change')) {
        this._config[keys]['change'] = this.processChange(keys);
      }
    }
  }

  processFields(objectType: string): Object {
    const configObject = this._config[objectType];

    // Si pas de config, on retourne un objet vide
    if (!configObject) {
      console.log(`No config found for ${objectType}`);
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
    return configObject;
  }
  /**
   * Pour récupérer la function change qui précise la procédure en cas de changement de valeur du formulaire
   * @param objectType
   */
  processChange(objectType: string) {
    const configObject = this._config[objectType];
    const change = configObject.change;
    return this.toFunction(change);
  }

  getChildsByObjectType(objectType) {
    let resultats: string[] = [];
    function findKeyValues(obj, cleRecherchee) {
      for (const cle in obj) {
        if (obj.hasOwnProperty(cle)) {
          if (cle === cleRecherchee && obj[cle] !== null) {
            resultats.push(...Object.keys(obj[cle]));
          }
          if (typeof obj[cle] === 'object' && obj[cle] !== null) {
            findKeyValues(obj[cle], cleRecherchee);
          }
        }
      }
    }
    const tree = this._config['tree'];
    findKeyValues(tree, objectType);
    return resultats;
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
}
