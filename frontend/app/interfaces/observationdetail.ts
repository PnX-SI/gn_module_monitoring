import { JsonData } from '../types/jsondata';
import { IObject } from './object';

export interface IObservationDetail extends IObject {
  pk: number;
  data: JsonData;
  id_observation_detail: number;
  id_observation: number;
  id_base_visit: number;
  id_base_site: number;
  uuid_observation_detail: string;
  meta_create_date: Date;
  meta_update_date: Date;
}
