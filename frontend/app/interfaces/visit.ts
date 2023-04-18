import { JsonData } from "../types/jsondata";
import { IObject } from "./object";

export interface IVisit extends IObject {
  pk:number;
  comments: string;
  data: JsonData;
  id_base_visit: number;
  id_module: number;
  id_nomenclature_grp_typ: number;
  id_nomenclature_tech_collect_campanule: number;
  meta_create_date: Date;
  meta_update_date: Date;
  nb_observations: number;
  uuid_base_visit: string;
  visit_date_max: Date;
  visit_date_min: Date;
}
