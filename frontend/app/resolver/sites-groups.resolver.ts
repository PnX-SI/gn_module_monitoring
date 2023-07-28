import { Injectable } from '@angular/core';
import { SitesGroupService, SitesService } from '../services/api-geom.service';
import { Observable, forkJoin } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { ISite, ISitesGroup } from '../interfaces/geom';
import { IPaginated } from '../interfaces/page';
import { IobjObs } from '../interfaces/objObs';
import { map } from 'rxjs/operators';
const LIMIT = 10;

@Injectable({ providedIn: 'root' })
export class SitesGroupsReslver
  implements
    Resolve<{
      sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
      sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
    }>
{
  constructor(
    public service: SitesGroupService,
    public serviceSite: SitesService
  ) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<{
    sitesGroups: { data: IPaginated<ISitesGroup>; objConfig: IobjObs<ISitesGroup> };
    sites: { data: IPaginated<ISite>; objConfig: IobjObs<ISite> };
  }> {
    const $getSiteGroups = this.service.get(1, LIMIT, {});
    const $configSitesGroups = this.service.initConfig();

    const $getSites = this.serviceSite.get(1, LIMIT, {});
    const $configSites = this.serviceSite.initConfig();

    return forkJoin([$getSiteGroups, $configSitesGroups, $getSites, $configSites]).pipe(
      map((result) => {
        return {
          sitesGroups: { data: result[0], objConfig: result[1] },
          sites: { data: result[2], objConfig: result[3] },
        };
      })
    );
  }
}
