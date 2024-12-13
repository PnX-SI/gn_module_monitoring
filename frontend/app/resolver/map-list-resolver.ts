import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class MapListResolver implements Resolve<{ moduleCode: string }> {
  constructor() {}

  resolve(route: ActivatedRouteSnapshot): { moduleCode: string } {
    return { moduleCode: route.params.moduleCode };
  }
}
