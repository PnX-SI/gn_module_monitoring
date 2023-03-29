import { Utils } from "./../../utils/utils";
import { Component, OnInit } from "@angular/core";
import { mergeMap } from "rxjs/operators";

/** services */
import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";
import { ConfigService } from "../../services/config.service";
import { get } from "https";

@Component({
  selector: "pnx-monitoring-modules",
  templateUrl: "./modules.component.html",
  styleUrls: ["./modules.component.css"],
})
export class ModulesComponent implements OnInit {
  modules: Array<any> = [];

  backendUrl: string;
  frontendModuleMonitoringUrl: string;
  urlApplication: string;
  moduleMonitoringCode: string;
  assetsDirectory: string;

  bLoading = false;

  constructor(
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _configService: ConfigService
  ) {}

  ngOnInit() {
    this.bLoading = true;
    this._configService
      .init()
      .pipe(
        mergeMap(
          this._dataMonitoringObjectService.getModules.bind(
            this._dataMonitoringObjectService
          )
        )
      )
      .subscribe((modules: Array<any>) => {
        this.modules = modules.filter((m) => m.cruved.R >= 1);
        this.backendUrl = this._configService.backendUrl();
        this.frontendModuleMonitoringUrl =
          this._configService.frontendModuleMonitoringUrl();
        this.moduleMonitoringCode = this._configService.moduleMonitoringCode();
        this.urlApplication = this._configService.urlApplication();
        this.assetsDirectory =
          `${this._configService.backendUrl()}/${this._configService.appConfig.MEDIA_URL}/monitorings/`;
        this.bLoading = false;
      });
  }
}
