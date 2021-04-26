import { Utils } from './../../utils/utils';
import { Component, OnInit } from '@angular/core';
import { mergeMap } from '@librairies/rxjs/operators';

/** services */
import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { MonitoringConfigService } from '../../services/config.service';
import { get } from 'https';

@Component({
  selector: 'pnx-monitoring-modules',
  templateUrl: './modules.component.html',
  styleUrls: ['./modules.component.css']
})
export class ModulesComponent implements OnInit {
  modules: Array<any> = [];

  backendUrl: string;
  frontendModuleMonitoringUrl: string;
  urlApplication: string;
  moduleMonitoringCode: string;

  bLoading = false;

  constructor(
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _monitoringConfigService: MonitoringConfigService
  ) { }

  ngOnInit() {
    this.bLoading = true;
    this._monitoringConfigService
      .init()
      .pipe(
        mergeMap(this._dataMonitoringObjectService.getModules.bind(this._dataMonitoringObjectService))
      )
      .subscribe((modules: Array<any>) => {
        this.modules = modules.filter(m => m.cruved.R >= 1);
        this.backendUrl = this._monitoringConfigService.backendUrl();
        this.frontendModuleMonitoringUrl = this._monitoringConfigService.frontendModuleMonitoringUrl();
        this.moduleMonitoringCode = this._monitoringConfigService.moduleMonitoringCode();
        this.urlApplication = this._monitoringConfigService.urlApplication();
        this.bLoading = false;
      });
  }

}
