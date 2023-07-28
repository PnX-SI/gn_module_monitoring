import { Injectable } from '@angular/core';
import { SitesGroupService } from '../services/api-geom.service';
import { Observable, of } from 'rxjs';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { ISitesGroup } from '../interfaces/geom';

@Injectable({ providedIn: 'root' })
export class CreateSiteResolver implements Resolve<ISitesGroup | null> {
  constructor(public service: SitesGroupService) {}

  resolve(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<ISitesGroup | null> {
    const siteGroupId = parseInt(route.paramMap.get('id'));
    const $getSiteGroups = this.service.getById(siteGroupId).pipe((result) => {
      return result;
    });
    return $getSiteGroups;
  }
}
