import { distinctUntilChanged } from 'rxjs/operators';
import { Component, OnInit, Input, Output, SimpleChanges, EventEmitter } from '@angular/core';

import { ConfigService } from '../../services/config.service';

import { Router } from '@angular/router';
import { ObjectService } from '../../services/object.service';
import { IBreadCrumb } from '../../interfaces/object';

@Component({
  selector: 'pnx-monitoring-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.css'],
})
export class BreadcrumbsComponent implements OnInit {
  public breadcrumbs: IBreadCrumb[] = [];
  private breadCrumbSubscription;

  @Input() bEdit: boolean;
  @Output() bEditChange = new EventEmitter<boolean>();

  public frontendModuleMonitoringUrl: string;

  constructor(
    private _configService: ConfigService,
    private _router: Router,
    private _objectService: ObjectService
  ) {}

  ngOnInit() {
    this.breadCrumbSubscription = this._objectService.currentDataBreadCrumb
      .pipe(distinctUntilChanged())
      .subscribe((breadCrumb) => {
        this.breadcrumbs = breadCrumb;
      });
  }

  onClick(elem) {
    this.bEditChange.emit(false);
    setTimeout(() => {
      if (elem) {
        const path = [
          'monitorings',
          'object',
          elem.module_code,
          elem.object_type === 'module' ? 'sites_group' : elem.object_type,
        ];

        if (!(elem.object_type === 'module')) {
          path.push(elem.id);
        }
        this._router.navigate(path, {
          queryParams: elem.params,
        });
      } else {
        this._router.navigate([this._configService.frontendModuleMonitoringUrl()]);
      }
    }, 100);
  }

  ngOnDestroy() {
    this.breadCrumbSubscription.unsubscribe();
  }
}
