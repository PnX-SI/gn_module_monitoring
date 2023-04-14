import { endPoints } from "../enum/endpoints";
import { JsonData } from "../types/jsondata";
import { ISite, ISitesGroup } from "./geom";
import { IVisit } from "./visit";
export type ObjDataType = ISite | ISitesGroup | IVisit | JsonData ;

export interface IobjObs<ObjDataType> {
  properties: ObjDataType;
  endPoint: endPoints;
  objectType: "site" | "sites_group" | "visits";
  label: string;
  addObjLabel: string;
  editObjLabel: string;
  addChildLabel: string;
  id: string | null;
  moduleCode: string;
  schema: JsonData;
  template: {
    fieldNames: [];
    fieldLabels: JsonData;
    fieldNamesList: [];
    fieldDefinitions: {};
  };
  dataTable: { colNameObj: {} };
}
