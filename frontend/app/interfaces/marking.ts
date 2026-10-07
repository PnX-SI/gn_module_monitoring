import { JsonData } from '../types/jsondata';
import { IObject } from './object';

export interface IMarking extends IObject {
  pk: number;
  data: JsonData;
  id_marking: number;
  uuid_marking: string;
  id_individual: number;
  id_module: number;
  id_digitiser: number;
  id_operator: number;
  marking_date: Date;
  id_base_marking_site: number;
  id_nomenclature_marking_type: number;
  marking_location: string;
  marking_code: string;
  marking_details: string;
}
