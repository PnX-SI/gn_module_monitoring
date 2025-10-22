import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { ConfigServiceG } from '../services/config-g.service';
import { Observable, of } from 'rxjs';
import { mergeMap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class DetailSitesGroupsResolver implements Resolve<{ moduleCode: string }> {
  constructor(private _configService: ConfigServiceG) {}

  resolve(route: ActivatedRouteSnapshot): Observable<{ moduleCode: string }> {
    return of({ moduleCode: route.params.moduleCode });
  }
}
