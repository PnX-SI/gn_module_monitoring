import { JsonData } from '../types/jsondata';
import { IObject } from './object';

export interface IObservation extends IObject {
  pk: number;
  data: JsonData;
  id_observation: number;
  id_base_visit: number;
  cd_nom: number;
  comments: string;
  uuid_observation: string;
  meta_create_date: Date;
  meta_update_date: Date;
}
