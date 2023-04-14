import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import { endPoints } from '../enum/endpoints';
import { IGeomService, ISite, ISiteType, ISitesGroup } from '../interfaces/geom';
import { IobjObs, ObjDataType } from '../interfaces/objObs';
import { IPaginated } from '../interfaces/page';
import { JsonData } from '../types/jsondata';
import { Resp } from '../types/response';
import { Utils } from '../utils/utils';
import { CacheService } from './cache.service';
import { ConfigJsonService } from './config-json.service';

@Injectable()
export class ApiGeomService implements IGeomService {
  public endPoint: endPoints;
  public objectObs: IobjObs<ObjDataType>;

  constructor(
    protected _cacheService: CacheService,
    protected _configJsonService: ConfigJsonService
  ) {
    this.init(this.endPoint, this.objectObs);
  }

  init(endPoint, objectObjs) {
    this.endPoint = endPoint;
    this.objectObs = objectObjs;
    // this.endPoint = endPoints.sites_groups;
    // this.objectObs = {
    //   properties: {},
    //   endPoint: endPoints.sites_groups,
    //   objectType: 'sites_group',
    //   label: 'groupe de site',
    //   addObjLabel: 'Ajouter',
    //   editObjLabel: 'Editer',
    //   id: null,
    //   moduleCode: 'generic',
    //   schema: {},
    //   template: {
    //     fieldNames: [],
    //     fieldLabels: {},
    //     fieldNamesList: [],
    //     fieldDefinitions: {},
    //   },
    //   dataTable: { colNameObj: {} },
    // };
  }
  get(
    page: number = 1,
    limit: number = 10,
    params: JsonData = {}
  ): Observable<IPaginated<ISitesGroup | ISite>> {
    return this._cacheService.request<Observable<IPaginated<ISitesGroup | ISite>>>(
      'get',
      this.endPoint,
      {
        queryParams: { page, limit, ...params },
      }
    );
  }

  getById(id: number): Observable<ISitesGroup | ISite> {
    return this._cacheService.request<Observable<ISitesGroup | ISite>>(
      'get',
      `${this.endPoint}/${id}`
    );
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

  patch(id: number, updatedData: { properties: ISitesGroup | ISite }): Observable<Resp> {
    return this._cacheService.request('patch', `${this.endPoint}/${id}`, {
      postData: updatedData,
    });
  }

  create(postData: { properties: ISitesGroup | ISite }): Observable<Resp> {
    return this._cacheService.request('post', `${this.endPoint}`, {
      postData: postData,
    });
  }

  delete(id: number): Observable<Resp> {
    return this._cacheService.request('delete', `${this.endPoint}/${id}`);
  }
}

@Injectable()
export class SitesGroupService extends ApiGeomService {
  constructor(_cacheService: CacheService, _configJsonService: ConfigJsonService) {
    super(_cacheService, _configJsonService);
  }
  init(): void {
    this.endPoint = endPoints.sites_groups;
    this.objectObs = {
      properties: {},
      endPoint: endPoints.sites_groups,
      objectType: 'sites_group',
      label: 'groupe de site',
      addObjLabel: 'Ajouter un nouveau groupe de site',
      editObjLabel: 'Editer le groupe de site',
      id: null,
      moduleCode: 'generic',
      schema: {},
      template: {
        fieldNames: [],
        fieldLabels: {},
        fieldNamesList: [],
        fieldDefinitions: {},
      },
      dataTable: { colNameObj: {} },
    };
    this._configJsonService
      .init(this.objectObs.moduleCode)
      .pipe()
      .subscribe(() => {
        const fieldNames = this._configJsonService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_properties'
        );
        const fieldNamesList = this._configJsonService.configModuleObjectParam(
          this.objectObs.moduleCode,
          this.objectObs.objectType,
          'display_list'
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
        this.objectObs.dataTable.colNameObj = Utils.toObject(fieldNamesList, fieldLabels);
      });
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

  addObjectType(): string {
    return 'un nouveau groupe de site';
  }

  editObjectType(): string {
    return 'le groupe de site';
  }
}

@Injectable()
export class SitesService extends ApiGeomService {
  constructor(_cacheService: CacheService, _configJsonService: ConfigJsonService) {
    super(_cacheService, _configJsonService);
  }
  opts = [];

  init(): void {
    this.endPoint = endPoints.sites;
    this.objectObs = {
      properties: {},
      endPoint: endPoints.sites,
      objectType: 'site',
      label: 'site',
      addObjLabel: 'Ajouter un nouveau site',
      editObjLabel: 'Editer le site',
      id: null,
      moduleCode: 'generic',
      schema: {},
      template: {
        fieldNames: [],
        fieldLabels: {},
        fieldNamesList: [],
        fieldDefinitions: {},
      },
      dataTable: { colNameObj: {} },
    };
    this._configJsonService
      .init(this.objectObs.moduleCode)
      .pipe()
      .subscribe(() => {
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
        this.objectObs.dataTable.colNameObj = Utils.toObject(fieldNamesList, fieldLabels);
      });
  }

  // getTypeSites(
  // ): Observable<IPaginated<ISiteType>> {
  //   return this._cacheService.request<Observable<IPaginated<ISiteType>>>(
  //     "get",
  //     "sites/types"
  //   );
  // }

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

  addObjectType(): string {
    return ' un nouveau site';
  }

  editObjectType(): string {
    return 'le site';
  }
}
