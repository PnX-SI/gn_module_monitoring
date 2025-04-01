import { Component, OnInit } from '@angular/core';
import { concatMap, map } from 'rxjs/operators';

/** services */
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { ConfigService } from '../../services/config.service';
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

  assetsDirectory: string;

  bLoading = false;

  toolTipNotAllowed: string = TOOLTIPMESSAGEALERT;

  constructor(
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _configService: ConfigService,
    private _permissionService: PermissionService
  ) {}

  ngOnInit() {
    this.bLoading = true;

    // Paramètre d'affichage
    this.assetsDirectory = `${this._configService.backendUrl()}/${
      this._configService.appConfig.MEDIA_URL
    }/monitorings/`;
    this.description = this._configService.descriptionModule();
    this.titleModule = this._configService.titleModule();

    // Récupération des permissions et de la liste des modules
    return this._dataMonitoringObjectService
      .getCruvedMonitoring()
      .pipe(
        map((listObjectCruved: Object) => {
          this._permissionService.setPermissionMonitorings(listObjectCruved);
        }),
        concatMap(() => this._dataMonitoringObjectService.getModules())
      )
      .subscribe((modules) => {
        this.currentPermission = this._permissionService.getPermissionUser();
        this.canAccessSite =
          this.currentPermission.MONITORINGS_SITES.canRead ||
          this.currentPermission.MONITORINGS_GRP_SITES.canRead;
        this.modules = modules.filter((m) => m.cruved.R >= 1);
        this.bLoading = false;
      });
  }
}
