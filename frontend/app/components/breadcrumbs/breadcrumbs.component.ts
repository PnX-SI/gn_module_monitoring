import { of } from 'rxjs';
import { mergeMap } from 'rxjs/operators';

import { Component, OnInit, Input, Output, SimpleChanges, EventEmitter } from '@angular/core';

import { DataMonitoringObjectService } from '../../services/data-monitoring-object.service';
import { ConfigService } from '../../services/config.service';

import { MonitoringObject } from "../../class/monitoring-object";
import { Router } from "@angular/router";
import { ActivatedRoute } from "@angular/router";
import { ObjectService } from "../../services/object.service";
import { SiteSiteGroup } from "../../interfaces/objObs";

@Component({
  selector: 'pnx-monitoring-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.css'],
})
export class BreadcrumbsComponent implements OnInit {
  public breadcrumbs;

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  public frontendModuleMonitoringUrl: string;

  @Input() obj: MonitoringObject;
  // Specific to the site access
  siteSiteGroup: SiteSiteGroup | null = null;

  constructor(
    private _dataMonitoringObjectService: DataMonitoringObjectService,
    private _configService: ConfigService,
    private _router: Router,
    private _route: ActivatedRoute,
    private _objectService: ObjectService
  ) {}

  ngOnInit() {
    if (this.obj === undefined) {
      this._objectService.currentObjectTypeParent.subscribe((parent) => {
        console.log(this.siteSiteGroup)
        if (parent.schema) {
          if (parent.objectType == 'sites_group') {
            this.siteSiteGroup = {
              siteGroup: parent,
              site: null,
            };
          } else if (parent.objectType == 'site' && this.siteSiteGroup?.siteGroup) {
            this.siteSiteGroup = {
              ...this.siteSiteGroup,
              site: parent,
            };
          }
        }
      });
    }
  }
    // this.initBreadcrumbs();

  initBreadcrumbs() {
    if (this.obj.deleted) {
      return;
    }
    this._configService
      .init(this.obj.moduleCode)
      .pipe(
        mergeMap(() => {
          if (!this.obj.moduleCode || this.obj.deleted) {
            return of([]);
          }

          const params = this._route.snapshot.queryParams;

          return this._dataMonitoringObjectService.getBreadcrumbs(
            this.obj.moduleCode,
            this.obj.objectType,
            this.obj.id,
            params
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
        this._router.navigate(
          [
            this._configService.frontendModuleMonitoringUrl(),
            'object',
            elem.module_code,
            elem.object_type,
            elem.id,
          ],
          {
            queryParams: elem.params,
          }
        );
      } else {
        this._router.navigate([this._configService.frontendModuleMonitoringUrl()]);
      }
    }, 100);
  }

  ngOnChanges(changes: SimpleChanges) {
    console.log(this.siteSiteGroup)
    for (const propName of Object.keys(changes)) {
      const chng = changes[propName];
      const cur = chng.currentValue;
      const pre = chng.currentValue;
      switch (propName) {
        case 'obj':
          this.initBreadcrumbs();
          break;
      }
    }
  }
}
