import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { GeoJSON } from "geojson";

import { CacheService } from "./cache.service";
import { IGeomService, ISitesGroup, ISite } from "../interfaces/geom";
import { IPaginated } from "../interfaces/page";
import { JsonData } from "../types/jsondata";
import { Resp } from "../types/response";

export enum endPoints {
  sites_groups = "sites_groups",
  sites = "sites",
}

@Injectable()
export class ApiGeomService implements IGeomService {
  public objectType: endPoints = endPoints.sites_groups;

  constructor(protected _cacheService: CacheService) {
    this.init();
  }

  init() {
    this.objectType = endPoints.sites_groups;
  }
  get(
    page: number = 1,
    limit: number = 10,
    params: JsonData = {}
  ): Observable<IPaginated<ISitesGroup | ISite>> {
    return this._cacheService.request<
      Observable<IPaginated<ISitesGroup | ISite>>
    >("get", this.objectType, {
      queryParams: { page, limit, ...params },
    });
  }

  getById(id: number): Observable<ISitesGroup | ISite> {
    return this._cacheService.request<Observable<ISitesGroup | ISite>>(
      "get",
      `${this.objectType}/${id}`
    );
  }

  get_geometries(params: JsonData = {}): Observable<GeoJSON.FeatureCollection> {
    return this._cacheService.request<Observable<GeoJSON.FeatureCollection>>(
      "get",
      `${this.objectType}/geometries`,
      {
        queryParams: { ...params },
      }
    );
  }

  patch(id: number, updatedData: ISitesGroup | ISite): Observable<Resp> {
    return this._cacheService.request("patch", `${this.objectType}/${id}`, {
      postData: updatedData,
    });
  }

  create( postData: ISitesGroup | ISite): Observable<Resp> {
    return this._cacheService.request("post", `${this.objectType}`, {
      postData: postData,
    });
  }

  delete(id: number): Observable<Resp> {
    return this._cacheService.request("delete", `${this.objectType}/${id}`);
  }
  
}

@Injectable()
export class SitesGroupService extends ApiGeomService {
  constructor(_cacheService: CacheService) {
    super(_cacheService);
  }
  init(): void {
    this.objectType = endPoints.sites_groups;
  }

  getSitesChild(
    page: number = 1,
    limit: number = 10,
    params: JsonData = {}
  ): Observable<IPaginated<ISite>> {
    return this._cacheService.request<Observable<IPaginated<ISite>>>(
      "get",
      `sites`,
      {
        queryParams: { page, limit, ...params },
      }
    );
  }

  addObjectType(): string {
    return "un nouveau groupe de site";
  }

  editObjectType(): string {
    return "le groupe de site";
  }
}

@Injectable()
export class SitesService extends ApiGeomService {
  constructor(_cacheService: CacheService) {
    super(_cacheService);
  }
  init(): void {
    this.objectType = endPoints.sites;
  }
  addObjectType(): string {
    return " un nouveau site";
  }

  editObjectType(): string {
    return "le site";
  }
}
