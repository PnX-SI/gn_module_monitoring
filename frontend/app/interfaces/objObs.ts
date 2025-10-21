import { endPoints } from '../enum/endpoints';
import { JsonData } from '../types/jsondata';
import { ISite, ISitesGroup } from './geom';
import { IVisit } from './visit';

export type ObjDataType = ISite | ISitesGroup | IVisit;
export interface IobjObs<T> {
  properties: T | {};
  endPoint: endPoints;
  objectType: 'site' | 'sites_group' | 'visit' | 'individual';
  routeBase: 'site' | 'sites_group' | 'visit' | 'individual';
  label: string;
  childType?: string;
  id: string | null;
  moduleCode: string;
  schema: JsonData;
  template: {
    fieldNames: [];
    fieldLabels: JsonData;
    fieldNamesList: [];
    fieldDefinitions: {};
    labelList: string;
  };
  dataTable: { colNameObj: {} };
}

export interface SiteSiteGroup {
  site: IobjObs<ObjDataType> | null;
  siteGroup: IobjObs<ObjDataType>;
}
