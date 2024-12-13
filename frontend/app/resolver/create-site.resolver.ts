import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class CreateSiteResolver implements Resolve<{ moduleCode: string; id_sites_group: string }> {
  constructor() {}

  resolve(route: ActivatedRouteSnapshot): { moduleCode: string; id_sites_group: string } {
    return {
      moduleCode: route.parent.params.moduleCode ?? route.parent.parent.params.moduleCode,
      id_sites_group: route.queryParams.id_sites_group,
    };
  }
}
