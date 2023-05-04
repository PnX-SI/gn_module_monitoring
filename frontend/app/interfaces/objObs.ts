import { endPoints } from "../enum/endpoints";
import { JsonData } from "../types/jsondata";
import { ISite, ISitesGroup } from "./geom";
import { IVisit } from "./visit";

export type ObjDataType = ISite | ISitesGroup | IVisit ;
export interface IobjObs<T> {
  properties: T | {};
  endPoint: endPoints;
  objectType: "site" | "sites_group" | "visit";
  label: string;
  addObjLabel: string;
  editObjLabel: string;
  seeObjLabel: string,
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

export interface SiteSiteGroup {
  site: IobjObs<ObjDataType> | null,
  siteGroup: IobjObs<ObjDataType>
}