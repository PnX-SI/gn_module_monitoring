import { Injectable } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot } from '@angular/router';
import { CommonService } from '@geonature_common/service/common.service';
import { PermissionService } from './permission.service';
import { ObjectsPermissionMonitorings } from '../enum/objectPermission';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(
    public router: Router,
    private _permissionService: PermissionService,
    public commonService: CommonService
  ) {}
  canActivate(route: ActivatedRouteSnapshot): Observable<boolean> {
    let routeData = route.data;
    return this.checkPermission(routeData);
  }

  checkPermission(routeData): Observable<boolean> {
    return this._permissionService.currentPermissionObj.pipe(
      map((permissionUserObject) => {
        let isAllowed: boolean = false;
        const expectedPermission = routeData.expectedPermission;
        const objectPermission: ObjectsPermissionMonitorings[] = routeData.objectPermission;

        switch (expectedPermission) {
          case 'Read':
            isAllowed = objectPermission.some((objectPerm) => {
              return permissionUserObject[objectPerm].canRead == true;
            });
            break;
          case 'Create':
            isAllowed = objectPermission.some((objectPerm) => {
              return (
                permissionUserObject[objectPerm].canCreate == true &&
                permissionUserObject[objectPerm].canRead == true
              );
            });
            break;
          case 'Update':
            isAllowed = objectPermission.some((objectPerm) => {
              return (
                permissionUserObject[objectPerm].canUpdate == true &&
                permissionUserObject[objectPerm].canRead == true
              );
            });
            break;
        }
        if (!isAllowed) {
          this.commonService.translateToaster(
            'warning',
            "Vous n'avez pas les droits pour accéder à la page"
          );
        }
        return isAllowed;
      })
    );
  }
}
