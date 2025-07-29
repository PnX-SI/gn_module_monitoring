import { JsonData } from '../types/jsondata';
import { IObject } from './object';

export interface IIndividual extends IObject {
  id_individual: number;
  uuid_individual: string;
  individual_name: string;
  cd_nom: number;
  id_nomenclature_sex: number;
  active: boolean;
  comment: string;
  id_digitiser: number;
  meta_create_date: Date;
  meta_update_date: Date;
}
