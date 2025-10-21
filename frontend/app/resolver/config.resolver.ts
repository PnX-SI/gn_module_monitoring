// resolver.service.ts
import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { Observable, of, EMPTY } from 'rxjs';
import { ConfigServiceG } from '../services/config-g.service';
import { mergeMap } from 'rxjs/operators';
@Injectable({
  providedIn: 'root',
})
export class ModuleConfigResolver implements Resolve<any> {
  constructor(private configServiceG: ConfigServiceG) {}

  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> {
    const moduleCode = route.params?.moduleCode;
    if (moduleCode) {
      return this.configServiceG.init(moduleCode).pipe(
        mergeMap((data) => {
          return of({ moduleCode: route.params.moduleCode });
        })
      );
    }
    return EMPTY;
  }
}
