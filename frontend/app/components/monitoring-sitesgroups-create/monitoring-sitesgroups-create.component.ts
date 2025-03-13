import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { ActivatedRoute } from '@angular/router';
import { mergeMap } from 'rxjs/operators';
import { endPoints } from '../../enum/endpoints';
import { ISitesGroup } from '../../interfaces/geom';
import { FormService } from '../../services/form.service';
import { SitesGroupService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { GeoJSONService } from '../../services/geojson.service';
import { MonitoringObject } from '../../class/monitoring-object';
import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigService } from '../../services/config.service';
import { IBreadCrumb } from '../../interfaces/object';
import { breadCrumbElementBase } from '../breadcrumbs/breadcrumbs.component';

@Component({
  selector: 'monitoring-sitesgroups-create',
  templateUrl: './monitoring-sitesgroups-create.component.html',
  styleUrls: ['./monitoring-sitesgroups-create.component.css'],
})
export class MonitoringSitesGroupsCreateComponent implements OnInit {
  siteGroup: ISitesGroup;
  objForm: FormGroup;
  urlRelative: string;
  currentUser: User;

  obj: MonitoringObject;
  bEdit: boolean = true;

  breadCrumbList: IBreadCrumb[] = [];
  breadCrumbElemnt: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;

  moduleCode: string;

  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _objService: ObjectService,
    public sitesGroupService: SitesGroupService,
    public geojsonService: GeoJSONService,
    private _monitoringObjServiceMonitoring: MonitoringObjectService,
    private _configService: ConfigService,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.moduleCode = this._route.snapshot.data.createSitesGroups.moduleCode;

    this.bEdit = true;
    this.objForm = this._formBuilder.group({});

    const elements = document.getElementsByClassName('monitoring-map-container');
    if (elements.length >= 1) {
      elements[0].remove();
    }

    this.obj = new MonitoringObject(
      this.moduleCode,
      'sites_group',
      null,
      this._monitoringObjServiceMonitoring
    );
    this.currentUser = this._auth.getCurrentUser();

    this._route.paramMap
      .pipe(
        mergeMap(() => {
          return this._configService.init(this.moduleCode);
        }),
        mergeMap(() => {
          return this.obj.get(0);
        })
      )
      .subscribe((params) => {
        this.obj.initTemplate();
        this._formService.changeFormMapObj({
          frmGp: this.objForm,
          bEdit: true,
          obj: this.obj,
        });
        this.updateBreadCrumb();
        this.obj.bIsInitialized = true;
      });
  }

  updateBreadCrumb() {
    const breadcrumb: IBreadCrumb[] = [];

    if (this.moduleCode !== 'generic') {
      const module = this._configService.config()[this.moduleCode].module;
      breadcrumb.push({
        description: module.module_label,
        label: '',
        url: `object/${module.module_code}/sites_group`,
      });
    }

    this.breadCrumbElementBase = {
      ...this.breadCrumbElementBase,
      url: `object/${this.moduleCode}/site`,
    };

    this.breadCrumbList = [...breadcrumb, this.breadCrumbElementBase];

    this._objService.changeBreadCrumb(this.breadCrumbList, true);
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesGroupFeatureGroup);
  }
}
