import { Observable } from "rxjs/Observable";
import "rxjs/add/observable/of";

import { Component, OnInit, Input } from "@angular/core";

import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";
import { ConfigService } from "./../../services/config.service";

import { MonitoringObject } from "../../class/monitoring-object";

@Component({
  selector: "pnx-monitoring-breadcrumps",
  templateUrl: "./breadcrumps.component.html",
  styleUrls: ["./breadcrumps.component.css"]
})
export class BreadcrumpsComponent implements OnInit {
  public breadcrumps;

  public frontendModuleMonitoringUrl: string;

  @Input() obj: MonitoringObject;

  constructor(
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _configService: ConfigService
  ) {}

  ngOnInit() {
    this._configService
      .init()
      .flatMap(() => {
        if (!this.obj.modulePath) {
          return Observable.of([]);
        }

        if (!this.obj.id && this.obj.parentId) {
          return this._dataMonitoringObjectService.getBreadcrumps(
            this.obj.modulePath,
            this.obj.parentType(),
            this.obj.parentId
          );
        }

        return this._dataMonitoringObjectService.getBreadcrumps(
          this.obj.modulePath,
          this.obj.objectType,
          this.obj.id
        );
      })
      .subscribe(breadcrumps => {
        this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
        this.breadcrumps = breadcrumps;
      });
  }
}
