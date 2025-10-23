import { Injectable } from '@angular/core';
import { Observable, of, forkJoin } from 'rxjs';
import { map, mergeMap } from 'rxjs/operators';
import { endPoints } from '../enum/endpoints';
import {
  IGeomObject,
  IGeomService,
  ISite,
  ISiteField,
  ISiteType,
  ISitesGroup,
} from '../interfaces/geom';
import { IobjObs } from '../interfaces/objObs';
import { IPaginated } from '../interfaces/page';
import { JsonData } from '../types/jsondata';
import { buildObjectResolvePropertyProcessing, Utils } from '../utils/utils';
import { CacheService } from './cache.service';
import { IVisit } from '../interfaces/visit';
import { IIndividual } from '../interfaces/individual';
import { IObject, IObjectProperties, IService } from '../interfaces/object';
import { LIMIT } from '../constants/api';
import { Module } from '../interfaces/module';
import { MonitoringObjectService } from './monitoring-object.service';
import { ConfigServiceG } from './config-g.service';

@Injectable()
export class ApiService<T = IObject> implements IService<T> {
  public objectObs: IobjObs<T>;
  public endPoint: endPoints;

  constructor(
    protected _cacheService: CacheService,
    protected _configServiceG: ConfigServiceG,
    protected _monitoringObjectService: MonitoringObjectService
  ) {}

  init(endPoint: endPoints, objectObjs: IobjObs<T>) {
    this.endPoint = endPoint;
    this.objectObs = objectObjs;
    console.log(this._configServiceG.config());
    // souscrit au sujet config du module en cours
    // quand le module change
    // test if config exist pour le module
    // sinon raise
    // lancer opération de initConfig
  }

  public initConfig(): IobjObs<T> {
    const config = (this._configServiceG.config() || {})[this.objectObs.objectType];
    this.objectObs.moduleCode = this._configServiceG.moduleCode();
    if (!config) return null;
    this.objectObs['label'] = config['label'];
    return this.objectObs;
  }

  get(page: number = 1, limit: number = LIMIT, params: JsonData = {}): Observable<IPaginated<T>> {
    const module = !(this.objectObs.moduleCode === 'generic')
      ? 'refacto/' + this.objectObs.moduleCode + '/'
      : '';

    return this._cacheService.request<Observable<IPaginated<T>>>(
      'get',
      `${module}${this.objectObs.endPoint}`,
      {
        queryParams: { page, limit, ...params },
      }
    );
  }

  getResolved(page: number = 1, limit: number = LIMIT, params: JsonData = {}): Observable<any> {
    /**
     * getResolved
     *
     * Renvoie les données paginées d'un type d'objet avec les propriétés résolues.
     *  La résolution consiste transformer la valeur retournée par l'api par celle d'affichage
     *  en fonction des types de champs définis dans la configuration.
     * @param {number} [page=1] The page number to fetch.
     * @param {number} [limit=10] The number of items to fetch.
     * @param {Object} [params={}] The parameters to pass to the service.
     * @returns {Observable<any>}
     */
    const config = (this._configServiceG.config() || {})[this.objectObs.objectType];
    if (!config) {
      return of(null);
    }
    return this.get(page, limit, params).pipe(
      mergeMap((paginatedData: IPaginated<any>) => {
        const dataProcessingObservables = buildObjectResolvePropertyProcessing(
          paginatedData,
          config['fields'] || {},
          this._configServiceG.moduleCode(),
          this._configServiceG,
          this._cacheService
        );
        return forkJoin(dataProcessingObservables).pipe(map(([resolvedItems]) => resolvedItems));
      })
    );
  }

  getById(id: number, moduleCode: string = 'generic'): Observable<T> {
    return this._cacheService.request<Observable<T>>(
      'get',
      `${this.objectObs.endPoint}/${moduleCode}/${id}`
    );
  }

  getByIdResolved(id: number, moduleCode: string = 'generic'): Observable<any> {
    const config = (this._configServiceG.config() || {})[this.objectObs.objectType];
    if (!config) {
      return of(null);
    }
    return this.getById(id, moduleCode).pipe(
      mergeMap((data: any) => {
        const dataToResolve = { items: [data] };
        const dataProcessingObservables = buildObjectResolvePropertyProcessing(
          dataToResolve,
          config['fields'] || {},
          this._configServiceG.moduleCode(),
          this._configServiceG,
          this._cacheService
        );
        return forkJoin(dataProcessingObservables).pipe(
          map(([resolvedItems]) => {
            return resolvedItems.items[0];
          })
        );
      })
    );
  }

  patch(id: number, updatedData: IObjectProperties<T>): Observable<T> {
    return this._cacheService.request('patch', `${this.objectObs.endPoint}/${id}`, {
      postData: updatedData as {},
    });
  }

  create(postData: IObjectProperties<T>): Observable<T> {
    return this._cacheService.request('post', `${this.objectObs.endPoint}`, {
      postData: postData as {},
    });
  }

  delete(id: number, params: JsonData = {}): Observable<T> {
    // module_code
    return this._cacheService.request('delete', `${this.objectObs.endPoint}/${id}`, {
      queryParams: params,
    });
  }

  setModuleCode(moduleCode: string) {
    this.objectObs.moduleCode = moduleCode;
  }
}

@Injectable()
export class ApiGeomService<T = IGeomObject> extends ApiService<T> implements IGeomService<T> {
  constructor(
    protected _cacheService: CacheService,
    protected _configServiceG: ConfigServiceG,
    protected _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configServiceG, _monitoringObjectService);
    this.init(this.endPoint, this.objectObs);
  }

  get_geometries(params: JsonData = {}): Observable<GeoJSON.FeatureCollection> {
    // Suppression des champs avec des valeurs vides
    const clean_params = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null)
    );

    const endPoint = !(this.objectObs.moduleCode === 'generic')
      ? `refacto/${this.objectObs.moduleCode}/${this.endPoint}/geometries`
      : `${this.endPoint}/geometries`;

    return this._cacheService.request<Observable<GeoJSON.FeatureCollection>>('get', endPoint, {
      queryParams: { ...clean_params },
    });
  }

  getConfig(): Observable<T> {
    return this._cacheService.request('get', `${this.objectObs.endPoint}/config`);
  }
}

@Injectable()
export class SitesGroupService extends ApiGeomService<ISitesGroup> {
  constructor(
    _cacheService: CacheService,
    protected _configServiceG: ConfigServiceG,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configServiceG, _monitoringObjectService);
  }

  init(): void {
    const endPoint = endPoints.sites_groups;
    const objectObs: IobjObs<ISitesGroup> = {
      properties: {},
      endPoint: endPoints.sites_groups,
      objectType: 'sites_group',
      routeBase: 'sites_group',
      label: 'groupe de site',
      childType: 'site',
      id: null,
      moduleCode: 'generic',
      schema: {},
      template: {
        fieldNames: [],
        fieldLabels: {},
        fieldNamesList: [],
        fieldDefinitions: {},
        labelList: 'Groupes de sites',
      },
      dataTable: { colNameObj: {} },
    };
    super.init(endPoint, objectObs);
  }

  getSitesChild(
    page: number = 1,
    limit: number = 10,
    params: JsonData = {}
  ): Observable<IPaginated<ISite>> {
    const module = !(this.objectObs.moduleCode === 'generic')
      ? 'refacto/' + this.objectObs.moduleCode + '/'
      : '';
    return this._cacheService.request<Observable<IPaginated<ISite>>>(
      'get',
      `${module}${endPoints.sites}`,
      {
        queryParams: { page, limit, ...params },
      }
    );
  }

  getSitesChildResolved(
    page: number = 1,
    limit: number = LIMIT,
    params: JsonData = {},
    fieldsConfig = {}
  ): Observable<any> {
    /**
     * getSitesChildResolved
     * Renvoie les sites enfants d'un groupe de site avec les propriétés résolues.
     *  La résolution consiste transformer la valeur retournée par l'api par celle d'affichage
     *  en fonction des types de champs définis dans la configuration.
     * @param {number} [page=1] The page number to fetch.
     * @param {number} [limit=10] The number of items to fetch.
     * @param {Object} [params={}] The parameters to pass to the service.
     * @param {Object} [fieldsConfig={}] The configuration of fields to resolve.
     * @returns {Observable<any>}
     */
    return this.getSitesChild(page, limit, params).pipe(
      mergeMap((paginatedData: IPaginated<any>) => {
        const dataProcessingObservables = buildObjectResolvePropertyProcessing(
          paginatedData,
          fieldsConfig,
          this.objectObs.moduleCode,
          this._configServiceG,
          this._cacheService
        );
        return forkJoin(dataProcessingObservables).pipe(map(([resolvedItems]) => resolvedItems));
      })
    );
  }
}

@Injectable()
export class SitesService extends ApiGeomService<ISite> {
  constructor(
    _cacheService: CacheService,
    protected _configServiceG: ConfigServiceG,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configServiceG, _monitoringObjectService);
  }

  init(): void {
    const endPoint = endPoints.sites;
    const objectObs: IobjObs<ISite> = {
      properties: {},
      endPoint: endPoints.sites,
      objectType: 'site',
      routeBase: 'site',
      label: 'site',
      childType: 'visit',
      id: null,
      moduleCode: 'generic',
      schema: {},
      template: {
        fieldNames: [],
        fieldLabels: {},
        fieldNamesList: [],
        fieldDefinitions: {},
        labelList: 'Sites',
      },
      dataTable: { colNameObj: {} },
    };
    super.init(endPoint, objectObs);
  }

  getTypeSites(
    page: number = 1,
    limit: number = 10,
    params: JsonData = {}
  ): Observable<IPaginated<ISiteType>> {
    return this._cacheService.request<Observable<IPaginated<ISiteType>>>(
      'get',
      'sites/types/label',
      {
        queryParams: { page, limit, ...params },
      }
    );
  }

  getTypesSiteByIdSite(idSite: number): Observable<any> {
    return this._cacheService.request<Observable<any>>('get', `sites/${idSite}/types`);
  }

  getTypesSiteById(idTypeSite: number): Observable<any> {
    return this._cacheService.request<Observable<any>>('get', `sites/types/${idTypeSite}`);
  }

  getSiteModules(idSite: number, moduleCode: string = 'generic'): Observable<Module[]> {
    return this._cacheService.request('get', `sites/${moduleCode}/${idSite}/modules`);
  }
}

@Injectable()
export class VisitsService extends ApiService<IVisit> {
  constructor(
    _cacheService: CacheService,
    protected _configServiceG: ConfigServiceG,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configServiceG, _monitoringObjectService);
    this.init();
  }
  init(): void {
    const endPoint = endPoints.visits;
    const objectObs: IobjObs<IVisit> = {
      properties: {},
      endPoint: endPoints.visits,
      objectType: 'visit',
      label: 'visite',
      childType: 'observation',
      routeBase: 'visit',
      id: null,
      moduleCode: 'generic',
      schema: {},
      template: {
        fieldNames: [],
        fieldLabels: {},
        fieldNamesList: [],
        fieldDefinitions: {},
        labelList: 'Visites',
      },
      dataTable: { colNameObj: {} },
    };
    super.init(endPoint, objectObs);
  }
}

@Injectable()
export class IndividualsService extends ApiService<IIndividual> {
  constructor(
    _cacheService: CacheService,
    protected _configServiceG: ConfigServiceG,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configServiceG, _monitoringObjectService);
    this.init();
  }
  init(): void {
    const endPoint = endPoints.individuals;
    const objectObs: IobjObs<IIndividual> = {
      properties: {},
      endPoint: endPoints.individuals,
      objectType: 'individual',
      label: 'individu',
      childType: 'marking',
      routeBase: 'individual',
      id: null,
      moduleCode: 'generic',
      schema: {},
      template: {
        fieldNames: [],
        fieldLabels: {},
        fieldNamesList: [],
        fieldDefinitions: {},
        labelList: 'Individus',
      },
      dataTable: { colNameObj: {} },
    };
    super.init(endPoint, objectObs);
  }
}
