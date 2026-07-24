import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { ConfigServiceG } from '../services/config-g.service';
import { Observable, of } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DetailObservationsDetailResolver implements Resolve<{ moduleCode: string }> {
  constructor(private _configServiceG: ConfigServiceG) {}

  resolve(route: ActivatedRouteSnapshot): Observable<{ moduleCode: string }> {
    return of({ moduleCode: route.params.moduleCode });
  }
}
