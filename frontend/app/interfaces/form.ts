import { JsonData } from "../types/jsondata";
import { ISite, ISitesGroup } from "./geom";

export interface IDataForm extends JsonData, ISitesGroup, ISite {
    patch_update:number
  }
  