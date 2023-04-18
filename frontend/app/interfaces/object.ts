import { JsonData } from "../types/jsondata";
import { IPaginated } from "./page";
import { GeoJSON } from "geojson";
import { Observable } from "rxjs";

export interface IObject {
  data: JsonData;
}

export interface IObjectProperties<T> {
  properties: T;
}

export interface IService<T> {
  get(limit: number, page: number, params: JsonData): Observable<IPaginated<T>>;
  create(postdata: IObjectProperties<T>): Observable<T>;
  patch(id: number, updatedData: IObjectProperties<T>): Observable<T>;
  delete(id: number): Observable<T>;
}

export type SelectObject = {
  id: string;
  label: string;
};

