import { GeoJSON } from 'geojson';
import { Observable } from 'rxjs';
import { JsonData } from '../types/jsondata';
import { IObject, IService } from './object';

export interface IGeomObject extends IObject {
  geometry: GeoJSON.Geometry;
}

export interface ISitesGroup extends IGeomObject {
  pk: number;
  comments?: string;
  id_sites_group: number;
  nb_sites: number;
  nb_visits: number;
  sites_group_code: string;
  sites_group_description: string;
  sites_group_name: string;
  uuid_sites_group: string; //FIXME: see if OK
}

export interface ISite extends IGeomObject {
  pk: number;
  altitude_max: number;
  altitude_min: number;
  base_site_code: string;
  base_site_description?: string;
  base_site_name: string;
  first_use_date: string;
  id_base_site: number;
  id_nomenclature_type_site?: number;
  last_visit?: Date;
  meta_create_date: Date;
  meta_update_date: Date;
  nb_visits: number;
  uuid_base_site: string;
}

export interface IGeomService<IGeomObject> extends IService<IGeomObject> {
  get_geometries(params: JsonData): Observable<GeoJSON.FeatureCollection>;
}

export interface ISiteType {
  config: JsonData;
  id_nomenclature_type_site: number;
  label: string;
}

export interface ISiteType {
  config:JsonData,
  id_nomenclature_type_site:number,
  label:string
}