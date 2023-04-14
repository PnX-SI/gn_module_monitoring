import { endPoints } from "../enum/endpoints";
import { JsonData } from "../types/jsondata";
import { ISite, ISitesGroup } from "./geom";

export type ObjDataType = ISite | ISitesGroup | JsonData;

export interface IobjObs<ObjDataType> {
  properties: ObjDataType;
  endPoint: endPoints;
  objectType: "site" | "sites_group";
  label: string;
  addObjLabel: string;
  editObjLabel: string;
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
