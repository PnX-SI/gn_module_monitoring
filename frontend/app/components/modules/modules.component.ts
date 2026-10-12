import { Component, OnInit } from '@angular/core';
import { concatMap, map } from 'rxjs/operators';

/** services */
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { ConfigServiceG } from '../../services/config-g.service';
import { ConfigService as GnConfigService } from '@geonature/services/config.service';
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
    private _configServiceG: ConfigServiceG,
    private _geonatureConfig: GnConfigService,
    private _permissionService: PermissionService
  ) {}

  ngOnInit() {
    this.bLoading = true;

    // Paramètre d'affichage
    this.assetsDirectory = `${this._configServiceG.backendUrl()}/${
      this._geonatureConfig.MEDIA_URL
    }/monitorings/`;
    this.description = this._geonatureConfig.MONITORINGS.DESCRIPTION_MODULE;
    this.titleModule = this._geonatureConfig.MONITORINGS.TITLE_MODULE;

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
