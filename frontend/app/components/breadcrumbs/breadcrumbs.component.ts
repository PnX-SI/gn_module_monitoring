import { of } from "@librairies/rxjs";
import { mergeMap } from "@librairies/rxjs/operators";

import {
  Component,
  OnInit,
  Input,
  Output,
  SimpleChanges,
  EventEmitter,
} from "@angular/core";

import { DataMonitoringObjectService } from "../../services/data-monitoring-object.service";
import { ConfigService } from "../../services/config.service";

import { MonitoringObject } from "../../class/monitoring-object";
import { Router } from "@angular/router";

@Component({
  selector: "pnx-monitoring-breadcrumbs",
  templateUrl: "./breadcrumbs.component.html",
  styleUrls: ["./breadcrumbs.component.css"],
})
export class BreadcrumbsComponent implements OnInit {
  public breadcrumbs;

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  public frontendModuleMonitoringUrl: string;

  @Input() obj: MonitoringObject;

  constructor(
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _configService: ConfigService,
    private _router: Router
  ) {}

  ngOnInit() {
    // this.initBreadcrumbs();
  }

  initBreadcrumbs() {
    this._configService
      .init(this.obj.modulePath)
      .pipe(
        mergeMap(() => {
          if (!this.obj.modulePath) {
            return of([]);
          }

          if (!this.obj.id && this.obj.parentId) {
            return this._dataMonitoringObjectService.getbreadcrumbs(
              this.obj.modulePath,
              this.obj.parentType(),
              this.obj.parentId
            );
          }

          return this._dataMonitoringObjectService.getbreadcrumbs(
            this.obj.modulePath,
            this.obj.objectType,
            this.obj.id
          );
        })
      )
      .subscribe((breadcrumbs) => {
        this.frontendModuleMonitoringUrl = this._configService.frontendModuleMonitoringUrl();
        this.breadcrumbs = breadcrumbs;
      });
  }

  onClick(elem) {
    this.bEditChange.emit(false);
    setTimeout(() => {
      if (elem) {
        this._router.navigate([
          "/",
          this._configService.frontendModuleMonitoringUrl(),
          "object",
          elem.module_path,
          elem.object_type,
          elem.id,
        ]);
      } else {
        this._router.navigate([
          "/",
          this._configService.frontendModuleMonitoringUrl(),
        ]);
      }
    }, 100);
  }

  ngOnChanges(changes: SimpleChanges) {
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const pre = chng.currentValue;
      switch (propName) {
        case "obj":
          this.initBreadcrumbs();
          break;
      }
    }
  }
}
