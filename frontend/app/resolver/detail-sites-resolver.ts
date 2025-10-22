import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import { ConfigServiceG } from '../services/config-g.service';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class DetailSitesResolver implements Resolve<{ moduleCode: string }> {
  constructor(private _configServiceG: ConfigServiceG) {}

  resolve(route: ActivatedRouteSnapshot): Observable<{ moduleCode: string }> {
    return this._configServiceG.init(route.params.moduleCode).pipe(
      mergeMap((data) => {
        return of({
          moduleCode: route.parent.params.moduleCode ?? route.parent.parent.params.moduleCode,
        });
      })
    );
  }
}
