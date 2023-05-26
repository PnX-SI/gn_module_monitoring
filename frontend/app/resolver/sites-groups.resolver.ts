import { Injectable } from '@angular/core';
import { SitesGroupService } from '../services/api-geom.service';
import { Observable, forkJoin } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { ISitesGroup } from '../interfaces/geom';
import { IPaginated } from '../interfaces/page';
import { IobjObs } from '../interfaces/objObs';
import { map } from 'rxjs/operators';
const LIMIT = 10;

@Injectable({ providedIn: 'root' })
export class SitesGroupsReslver
  implements Resolve<{ sitesGroups: IPaginated<ISitesGroup>; objectObs: IobjObs<ISitesGroup> }>
{
  constructor(public service: SitesGroupService) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<{ sitesGroups: IPaginated<ISitesGroup>; objectObs: IobjObs<ISitesGroup> }> {
    const $getSiteGroups = this.service.get(1, LIMIT, {})
    const $configSitesGroups = this.service.initConfig()
    return forkJoin([$getSiteGroups,$configSitesGroups ]).pipe(map((result) => {
      return {
        sitesGroups: result[0],
        objectObs: result[1],
      };
    }));
  }
}
