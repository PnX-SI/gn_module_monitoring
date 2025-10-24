import { endPoints } from '../enum/endpoints';
import { JsonData } from '../types/jsondata';
import { ISite, ISitesGroup } from './geom';
import { IVisit } from './visit';

export type ObjDataType = ISite | ISitesGroup | IVisit;
export interface IobjObs<T> {
  endPoint: endPoints;
  objectType: 'site' | 'sites_group' | 'visit' | 'individual' | 'module';
  label: string;
  childType?: string;
  moduleCode: string; // Voir si utilisé
}

export interface SiteSiteGroup {
  site: IobjObs<ObjDataType> | null;
  siteGroup: IobjObs<ObjDataType>;
}
