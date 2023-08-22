import { Injectable } from '@angular/core';
import { SitesGroupService, SitesService } from '../services/api-geom.service';
import { Observable, forkJoin, of } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { ISite, ISitesGroup } from '../interfaces/geom';
import { IPaginated } from '../interfaces/page';
import { IobjObs } from '../interfaces/objObs';
import { map, mergeMap } from 'rxjs/operators';
import { ConfigJsonService } from '../services/config-json.service';
const LIMIT = 10;

@Injectable({ providedIn: 'root' })
export class SitesGroupsReslver
  implements
    Resolve<{
      sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
      sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
      route: string;
    }>
{
  constructor(
    public service: SitesGroupService,
    public serviceSite: SitesService,
    public _configJsonService : ConfigJsonService
  ) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<{
    sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
    sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
    route: string;
  }> {

    const $configSitesGroups = this.service.initConfig();
    const $configSites = this.serviceSite.initConfig();

    const resolvedData = forkJoin([$configSitesGroups,$configSites]).pipe(
      map((configs) => {
        
        const configSchemaSiteGroup= this._configJsonService.configModuleObject(
          configs[0].moduleCode,
          configs[0].objectType
        )

        const configSchemaSite= this._configJsonService.configModuleObject(
          configs[1].moduleCode,
          configs[1].objectType
        )
        
        const sortSiteGroupInit = "sorts" in configSchemaSiteGroup  ?{sort_dir:configSchemaSiteGroup.sorts[0].dir, sort:configSchemaSiteGroup.sorts[0].prop} : {};
        const sortSiteInit = "sorts" in configSchemaSite  ? {sort_dir:configSchemaSite.sorts[0].dir, sort:configSchemaSite.sorts[0].prop} : {};

        const $getSiteGroups = this.service.get(1, LIMIT,sortSiteGroupInit);
        const $getSites = this.serviceSite.get(1, LIMIT, sortSiteInit);
        
         return forkJoin([$getSiteGroups, $getSites]).pipe(
          map(([siteGroups,sites]) => {
            return  {
              sitesGroups: { data: siteGroups, objConfig:  configs[0] },
              sites: { data: sites, objConfig:  configs[1] },
              route: route['_urlSegment'].segments[1].path,
            }
          })
        )
      }),
      mergeMap((result) => {
        return result
      })
    )
    return resolvedData
}
}
