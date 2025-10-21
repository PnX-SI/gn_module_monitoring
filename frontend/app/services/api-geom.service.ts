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
import { ConfigService } from './config.service';

@Injectable()
export class ApiService<T = IObject> implements IService<T> {
  public objectObs: IobjObs<T>;
  public endPoint: endPoints;

  constructor(
    protected _cacheService: CacheService,
    protected _configService: ConfigService,
    protected _monitoringObjectService: MonitoringObjectService
  ) {}

  init(endPoint: endPoints, objectObjs: IobjObs<T>) {
    this.endPoint = endPoint;
    this.objectObs = objectObjs;
    // souscrit au sujet config du module en cours
    // quand le module change
    // test if config exist pour le module
    // sinon raise
    // lancer opération de initConfig
  }

  public initConfig(): Observable<IobjObs<T>> {
    return this._configService.init(this.objectObs.moduleCode).pipe(
      map(() => {
        const fieldNames = this._configService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_properties'
        );
        //FIXME: same as site group: to refact
        const fieldNamesList = this._configService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_list'
        );

        if (!fieldNamesList) {
          return null;
        }

        // Initialisation des différents labels de l'objet
        const objetLabels = this.getModuleObjetTypeLabels();
        Object.entries(objetLabels).forEach(([key, value]) => {
          this.objectObs[key] = value;
        });

        const labelList = this._configService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'label_list'
        );
        const schema = this._configService.schema(
          this.objectObs.moduleCode,
          this.objectObs.objectType
        );
        const fieldLabels = this._configService.fieldLabels(schema);
        const fieldDefinitions = this._configService.fieldDefinitions(schema);
        this.objectObs.template.fieldNames = fieldNames;
        this.objectObs.template.fieldNamesList = fieldNamesList;
        this.objectObs.schema = schema;
        this.objectObs.template.fieldLabels = fieldLabels;
        this.objectObs.template.fieldDefinitions = fieldDefinitions;
        this.objectObs.template.fieldNamesList = fieldNamesList;

        if (labelList != undefined) {
          this.objectObs.template.labelList = labelList;
        }
        this.objectObs.dataTable.colNameObj = Utils.toObject(fieldNamesList, fieldLabels);
        return this.objectObs;
      })
    );
  }

  protected getModuleObjetTypeLabels(): {} {
    const moduleCode = this.objectObs.moduleCode;
    const objectType = this.objectObs.objectType;
    const label = this._configService.configModuleObjectParam(moduleCode, objectType, 'label');


    let labels = {
      label: label,
    };

    return labels;
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
    return this.get(page, limit, params).pipe(
      mergeMap((paginatedData: IPaginated<any>) => {
        const dataProcessingObservables = buildObjectResolvePropertyProcessing(
          paginatedData,
          this.objectObs.schema,
          this.objectObs.moduleCode,
          this._monitoringObjectService,
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
    protected _configService: ConfigService,
    protected _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configService, _monitoringObjectService);
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
    _configService: ConfigService,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configService, _monitoringObjectService);
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
          this._monitoringObjectService,
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
    _configService: ConfigService,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configService, _monitoringObjectService);
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
    _configService: ConfigService,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configService, _monitoringObjectService);
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
    _configService: ConfigService,
    _monitoringObjectService: MonitoringObjectService
  ) {
    super(_cacheService, _configService, _monitoringObjectService);
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
