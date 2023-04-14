import { JsonData } from "../types/jsondata";
import { IPaginated } from "./page";
import { GeoJSON } from "geojson";
import { Observable } from "rxjs";
import { Resp } from "../types/response";

export interface IObject {
  data: JsonData;
}

export interface IService<T> {
  get(limit: number, page: number, params: JsonData): Observable<IPaginated<T>>;
  create(postdata: T): Observable<Resp>;
  patch(id: number, updatedData: T): Observable<Resp>;
  // delete(obj: IGeomObject)
}

export interface IGeomService<IGeomObject> extends IService<IGeomObject> {
  get_geometries(params: JsonData): Observable<GeoJSON.FeatureCollection>;
}
