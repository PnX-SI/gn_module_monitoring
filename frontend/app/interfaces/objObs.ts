import { endPoints } from '../enum/endpoints';
import { JsonData } from '../types/jsondata';
import { ISite, ISitesGroup } from './geom';
import { IVisit } from './visit';

export type ObjDataType = ISite | ISitesGroup | IVisit;
export interface IobjObs<T> {
  objectType:
    | 'site'
    | 'sites_group'
    | 'visit'
    | 'individual'
    | 'module'
    | 'observation'
    | 'observation_detail'
    | 'marking';
  childType?: string;
}

export interface SiteSiteGroup {
  site: IobjObs<ObjDataType> | null;
  siteGroup: IobjObs<ObjDataType>;
}
