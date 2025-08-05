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

  init(endPoint,  objectObjs) {
    this.endPoint = endPoint;
    this.objectObs = objectObjs;
    console.log("init");
    this._configService.currentModuleConfigObs.subscribe((value) => {
      console.log("init sub", value);
      if (value !== null) {
      console.log("init run initConfig", value, this.objectObs);
       this.initConfig()
      }
    })
  }

  public initConfig(): Observable<IobjObs<T>> {
    console.log("initConfig")
    this.objectObs.moduleCode = this._configService.currentModuleConfig?.module?.module_code;
    console.log("initConfig", this.objectObs.moduleCode )
     const fieldNames = this._configService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_properties'
        );
    console.log("fieldNames")
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
  }

  protected getModuleObjetTypeLabels(): {} {
    const moduleCode = this.objectObs.moduleCode;
    const objectType = this.objectObs.objectType;
    const childObjectType = this.objectObs.childType;

    const genre = this._configService.configModuleObjectParam(moduleCode, objectType, 'genre');
    const label = this._configService.configModuleObjectParam(moduleCode, objectType, 'label');

    let nouveauLabel = Utils.labelNew(genre, label);
    let articleDuLabel = Utils.labelDu(genre, label);
    let articleLabel = Utils.labelArtDef(genre, label);
    let articleUndefLabel = Utils.labelArtUndef(genre);

    let labels = {
      label: label,
      addObjLabel: `Ajouter ${articleUndefLabel} ${nouveauLabel} ${label.toLowerCase()}`,
      editObjLabel: `Editer ${articleLabel} ${label.toLowerCase()}`,
      seeObjLabel: `Consulter ${articleLabel} ${label.toLowerCase()}`,
      deleteObjLabel: `Supprimer ${articleLabel} ${label.toLowerCase()}`,
      detailObjLabel: `Detail ${articleDuLabel} ${label.toLowerCase()}`,
    };

    if (childObjectType) {
      const genreChild = this._configService.configModuleObjectParam(
        moduleCode,
        childObjectType,
        'genre'
      );
      const labelChild = this._configService.configModuleObjectParam(
        moduleCode,
        childObjectType,
        'label'
      );
      if (labelChild) {
        labels['addChildLabel'] = `Ajouter ${Utils.labelArtUndef(genreChild)} ${Utils.labelNew(
          genreChild,
          labelChild
        )} ${labelChild.toLowerCase()}`;
      }
    }
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

  getById(id: number): Observable<T> {
    return this._cacheService.request<Observable<T>>('get', `${this.objectObs.endPoint}/${id}`);
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
    // this.init(this.endPoint, this.objectObs);
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
      addObjLabel: 'Ajouter un nouveau groupe de site',
      editObjLabel: 'Editer le groupe de site',
      detailObjLabel: 'Détail du groupe de site',
      seeObjLabel: 'Consulter le groupe de site',
      addChildLabel: 'Ajouter un site',
      childType: 'site',
      deleteObjLabel: 'Supprimer le groupe de site',
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
      addObjLabel: 'Ajouter un nouveau site',
      editObjLabel: 'Editer le site',
      detailObjLabel: 'Détail du site',
      seeObjLabel: 'Consulter le site',
      deleteObjLabel: 'Supprimer le site',
      addChildLabel: 'Ajouter une visite',
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

  getSiteModules(idSite: number): Observable<Module[]> {
    return this._cacheService.request('get', `sites/${idSite}/modules`);
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
      addObjLabel: 'Ajouter une nouvelle visite',
      editObjLabel: 'Editer la visite',
      seeObjLabel: 'Consulter la visite',
      detailObjLabel: 'Détail de la visite',
      addChildLabel: 'Ajouter une observation',
      childType: 'observation',
      deleteObjLabel: 'Supprimer la visite',
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
      addObjLabel: 'Ajouter un nouvel individu',
      editObjLabel: 'Editer la individu',
      detailObjLabel: "Détail de  l'individu",
      seeObjLabel: "Consulter l'individu",
      addChildLabel: 'Ajouter un marquage',
      childType: 'marking',
      deleteObjLabel: "Supprimer l'individu",
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
