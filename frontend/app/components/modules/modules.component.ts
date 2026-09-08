import { Component, OnInit } from '@angular/core';
import { concatMap, map } from 'rxjs/operators';

/** services */
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { ConfigService } from '../../services/config.service';
import { TPermission } from '../../types/permission';
import { PermissionService } from '../../services/permission.service';
import { TOOLTIPMESSAGEALERT } from '../../constants/guard';

@Component({
  selector: 'pnx-monitoring-modules',
  templateUrl: './modules.component.html',
  styleUrls: ['./modules.component.css'],
})
export class ModulesComponent implements OnInit {
  canAccessSite: boolean = false;

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

    this._permissionService.setPermissionMonitorings('generic');

    // Récupération des permissions et de la liste des modules
    return this._dataMonitoringObjectService.getModules().subscribe((modules) => {
      const currentPermission = this._permissionService.setModulePermissions('generic');
      this.canAccessSite = currentPermission.site.R > 0 || currentPermission.sites_group.R > 0;
      this.modules = modules.filter((m) => m.cruved.R >= 1);
      this.bLoading = false;
    });
  }
}
