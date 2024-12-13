import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class CreateSitesGroupsResolver implements Resolve<{ moduleCode: string }> {
  constructor() {}

  resolve(route: ActivatedRouteSnapshot): { moduleCode: string } {
    return { moduleCode: route.parent.params.moduleCode };
  }
}
