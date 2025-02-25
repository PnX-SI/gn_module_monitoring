import { Utils } from './../../utils/utils';
import { Component, OnInit } from '@angular/core';
import { concatMap, map, mergeMap } from 'rxjs/operators';

/** services */
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { ConfigService } from '../../services/config.service';
import { get } from 'https';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { TPermission } from '../../types/permission';
import { ObjectsPermissionMonitorings } from '../../enum/objectPermission';
import { PermissionService } from '../../services/permission.service';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';

@Component({
  selector: 'pnx-monitoring-modules',
  templateUrl: './modules.component.html',
  styleUrls: ['./modules.component.css'],
})
export class ModulesComponent implements OnInit {
  currentUser: User;
  canAccessSite: boolean = false;
  currentPermission: TPermission = {
    [ObjectsPermissionMonitorings.MONITORINGS_GRP_SITES]: {
      canCreate: false,
      canRead: false,
      canUpdate: false,
      canDelete: false,
    },
    [ObjectsPermissionMonitorings.MONITORINGS_SITES]: {
      canCreate: false,
      canRead: false,
      canUpdate: false,
      canDelete: false,
    },
  };

  description: string;
  titleModule: string;
  modules: Array<any> = [];

  backendUrl: string;
  frontendModuleMonitoringUrl: string;
  urlApplication: string;
  moduleMonitoringCode: string;
  assetsDirectory: string;

  bLoading = false;

  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  constructor(
    private _auth: AuthService,
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _configService: ConfigService,
    private _permissionService: PermissionService
  ) {}

  ngOnInit() {
    this.bLoading = true;
    this._configService
      .init()
      .pipe(
        concatMap(() =>
          this._dataMonitoringObjectService.getCruvedMonitoring().pipe(
            map((listObjectCruved: Object) => {
              this._permissionService.setPermissionMonitorings(listObjectCruved);
            })
          )
        ),
        concatMap(() =>
          this._permissionService.currentPermissionObj.pipe(
            map((permissionObject: TPermission) => (this.currentPermission = permissionObject))
          )
        ),
        concatMap(
          this._dataMonitoringObjectService.getModules.bind(this._dataMonitoringObjectService)
        )
      )
      .subscribe((modules: Array<any>) => {
        this.modules = modules.filter((m) => m.cruved.R >= 1);
        this.backendUrl = this._configService.backendUrl();
        this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
        this.moduleMonitoringCode = this._configService.moduleMonitoringCode();
        this.urlApplication = this._configService.urlApplication();
        this.assetsDirectory = `${this._configService.backendUrl()}/${
          this._configService.appConfig.MEDIA_URL
        }/monitorings/`;
        this.bLoading = false;
        this.description = this._configService.descriptionModule();
        this.titleModule = this._configService.titleModule();

        this.canAccessSite =
          this.currentPermission.MONITORINGS_SITES.canRead ||
          this.currentPermission.MONITORINGS_GRP_SITES.canRead;
      });

    this.currentUser = this._auth.getCurrentUser();

    this.currentUser['cruved'] = {};
    this.currentUser['cruved_objects'] = {};
  }
}
