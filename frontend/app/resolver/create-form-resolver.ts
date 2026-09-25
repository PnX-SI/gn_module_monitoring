import { Injectable } from '@angular/core';
import { Resolve, ActivatedRouteSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ConfigServiceG } from '../services/config-g.service';
import { ObjectService } from '../services/object.service';
import { JsonData } from '../types/jsondata';

@Injectable({ providedIn: 'root' })
export class CreateFormResolver implements Resolve<{ moduleCode: string }> {
  constructor(
    private _configServiceG: ConfigServiceG,
    private _objectService: ObjectService
  ) {}

  resolve(route: ActivatedRouteSnapshot): Observable<{
    moduleCode: string;
    parents: any;
  }> {
    const moduleCode = route.parent.params.moduleCode ?? route.parent.parent.params.moduleCode;

    return this._objectService
      .loadParentsForCreation(route.queryParams, moduleCode, this._configServiceG.config())
      .pipe(
        map((parents: JsonData) => {
          return {
            moduleCode: moduleCode,
            parents: parents,
          };
        })
      );
  }
}
