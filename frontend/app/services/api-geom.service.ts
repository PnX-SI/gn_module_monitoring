import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
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
import { Utils } from '../utils/utils';
import { CacheService } from './cache.service';
import { ConfigJsonService } from './config-json.service';
import { IVisit } from '../interfaces/visit';
import { IObject, IObjectProperties, IService } from '../interfaces/object';
import { LIMIT } from '../constants/api';
import { Module } from '../interfaces/module';

@Injectable()
export class ApiService<T = IObject> implements IService<T> {
  public objectObs: IobjObs<T>;
  public endPoint: endPoints;
  constructor(
    protected _cacheService: CacheService,
    protected _configJsonService: ConfigJsonService
  ) { }

  init(endPoint: endPoints, objectObjs: IobjObs<T>) {
    this.endPoint = endPoint;
    this.objectObs = objectObjs;
  }

  public initConfig(): Observable<IobjObs<T>> {
    return this._configJsonService.init(this.objectObs.moduleCode).pipe(
      map(() => {
        const fieldNames = this._configJsonService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_properties'
        );
        //FIXME: same as site group: to refact
        const fieldNamesList = this._configJsonService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_list'
        );

        const labelList = this._configJsonService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'label_list'
        );
        const schema = this._configJsonService.schema(
          this.objectObs.moduleCode,
          this.objectObs.objectType
        );
        const fieldLabels = this._configJsonService.fieldLabels(schema);
        const fieldDefinitions = this._configJsonService.fieldDefinitions(schema);
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
  get(page: number = 1, limit: number = LIMIT, params: JsonData = {}): Observable<IPaginated<T>> {
    return this._cacheService.request<Observable<IPaginated<T>>>('get', this.objectObs.endPoint, {
      queryParams: { page, limit, ...params },
    });
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

  delete(id: number): Observable<T> {
    return this._cacheService.request('delete', `${this.objectObs.endPoint}/${id}`);
  }
}
@Injectable()
export class ApiGeomService<T = IGeomObject> extends ApiService<T> implements IGeomService<T> {
  constructor(
    protected _cacheService: CacheService,
    protected _configJsonService: ConfigJsonService
  ) {
    super(_cacheService, _configJsonService);
    this.init(this.endPoint, this.objectObs);
  }

  get_geometries(params: JsonData = {}): Observable<GeoJSON.FeatureCollection> {
    return this._cacheService.request<Observable<GeoJSON.FeatureCollection>>(
      'get',
      `${this.endPoint}/geometries`,
      {
        queryParams: { ...params },
      }
    );
  }

  getConfig(): Observable<T> {
    return this._cacheService.request('get', `${this.objectObs.endPoint}/config`);
  }
}

@Injectable()
export class SitesGroupService extends ApiGeomService<ISitesGroup> {
  constructor(_cacheService: CacheService, _configJsonService: ConfigJsonService) {
    super(_cacheService, _configJsonService);
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
      seeObjLabel: 'Consulter le groupe de site',
      addChildLabel: 'Ajouter un site',
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
    return this._cacheService.request<Observable<IPaginated<ISite>>>('get', `sites`, {
      queryParams: { page, limit, ...params },
    });
  }
}

@Injectable()
export class SitesService extends ApiGeomService<ISite> {
  constructor(_cacheService: CacheService, _configJsonService: ConfigJsonService) {
    super(_cacheService, _configJsonService);
  }

  init(): void {
    const endPoint = endPoints.sites;
    const objectObs: IobjObs<ISite> = {
      properties: {},
      endPoint: endPoints.sites,
      objectType: 'site',
      routeBase: 'sites',
      label: 'site',
      addObjLabel: 'Ajouter un nouveau site',
      editObjLabel: 'Editer le site',
      seeObjLabel: 'Consulter le site',
      deleteObjLabel: 'Supprimer le site',
      addChildLabel: 'Ajouter une visite',
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

  format_label_types_site(sites: ISite[]) {
    const rows_sites_table: ISiteField[] = [];
    for (const site of sites) {
      let list_label_types_site: string[] = [];
      const { types_site, ...rest_of_site } = site;
      for (const type_site of types_site) {
        if ('label' in type_site && typeof type_site['label'] == 'string') {
          list_label_types_site.push(type_site['label']);
        }
      }
      // Object.assign(rest_of_site,{types_site:list_label_types_site})
      rows_sites_table.push({ ...rest_of_site, types_site: list_label_types_site });
    }
    return rows_sites_table;
  }

  formatLabelTypesSite(sites: ISite[]) {
    const rowSitesTable: ISiteField[] = [];
    const varToFormat = 'types_site';
    const fieldToUse = 'label';
    for (const site of sites) {
      let listFieldToUse: string[] = [];
      const { [varToFormat]: _, ...rest_of_site } = site;
      for (const item of _) {
        if (Object.keys(item).includes(fieldToUse) && typeof item[fieldToUse] == 'string') {
          listFieldToUse.push(item[fieldToUse]);
        }
      }
      rowSitesTable.push({ ...rest_of_site, [varToFormat]: listFieldToUse });
    }
    return rowSitesTable;
  }
}

@Injectable()
export class VisitsService extends ApiService<IVisit> {
  constructor(_cacheService: CacheService, _configJsonService: ConfigJsonService) {
    super(_cacheService, _configJsonService);
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
      addChildLabel: 'Ajouter une observation',
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
