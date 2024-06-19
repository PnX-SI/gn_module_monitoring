import { Component, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Observable, of } from 'rxjs';
import { mergeMap, concatMap, tap } from 'rxjs/operators';

import { endPoints } from '../../enum/endpoints';
import { ISite, ISiteType } from '../../interfaces/geom';
import { IobjObs, ObjDataType, SiteSiteGroup } from '../../interfaces/objObs';
import { SitesGroupService, SitesService } from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { IPaginated } from '../../interfaces/page';
import { IBreadCrumb } from '../../interfaces/object';
import { breadCrumbElementBase } from '../breadcrumbs/breadcrumbs.component';
import { GeoJSONService } from '../../services/geojson.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';

import { MonitoringObjectService } from '../../services/monitoring-object.service';
import { ConfigService } from '../../services/config.service';
import { MonitoringObject } from '../../class/monitoring-object';

@Component({
  selector: 'monitoring-sites-create',
  templateUrl: './monitoring-sites-create.component.html',
  styleUrls: ['./monitoring-sites-create.component.css'],
})
export class MonitoringSitesCreateComponent implements OnInit {
  site: ISite;
  objForm: FormGroup;
  paramToFilt: string = 'label';
  funcToFilt: Function;
  titleBtn: string = 'Choix des types de sites';
  placeholderText: string = 'Sélectionnez les types de site';
  id_sites_group: number | null;
  types_site: string[];
  config: JsonData;
  objToCreate: IobjObs<ObjDataType>;
  urlRelative: string;

  breadCrumbList: IBreadCrumb[] = [];
  breadCrumbElemnt: IBreadCrumb = { label: 'Groupe de site', description: '' };
  breadCrumbElementBase: IBreadCrumb = breadCrumbElementBase;

  obj: MonitoringObject;
  bEdit: boolean = true;
  currentUser: User;
  constructor(
    private _auth: AuthService,
    private _formService: FormService,
    private _formBuilder: FormBuilder,
    private _sitesGroupService: SitesGroupService,
    public siteService: SitesService,
    private _objService: ObjectService,
    public geojsonService: GeoJSONService,
    private _monitoringObjServiceMonitoring: MonitoringObjectService,
    protected _configService: ConfigService,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    console.log('ngOnInit');
    this.bEdit = true;
    this.objForm = this._formBuilder.group({});

    const elements = document.getElementsByClassName('monitoring-map-container');
    if (elements.length >= 1) {
      elements[0].remove();
    }

    this.obj = new MonitoringObject('generic', 'site', null, this._monitoringObjServiceMonitoring);
    this.currentUser = this._auth.getCurrentUser();

    this._route.paramMap
      .pipe(
        mergeMap(() => {
          return this.initConfig();
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
        this.obj.bIsInitialized = true;
      });
  }

  onObjChanged(obj: MonitoringObject) {
    this.obj = obj;
  }

  initConfig(): Observable<any> {
    return this._configService.init().pipe(
      concatMap(() => {
        if (this.obj.objectType == 'site' && this.obj.id != null) {
          return this._monitoringObjServiceMonitoring
            .configService()
            .loadConfigSpecificConfig(this.obj)
            .pipe(
              tap((config) => {
                this.obj.template_specific = this._monitoringObjServiceMonitoring
                  .configService()
                  .addSpecificConfig(config);
              })
            );
        } else {
          return of(null);
        }
      }),
      mergeMap(() => {
        return of(true);
      })
    );
  }

  updateBreadCrumb(sitesGroup) {
    this.breadCrumbElemnt.description = sitesGroup.sites_group_name;
    this.breadCrumbElemnt.label = 'Groupe de site';
    this.breadCrumbElemnt['id'] = sitesGroup.id_sites_group;
    this.breadCrumbElemnt['objectType'] =
      this._sitesGroupService.objectObs.objectType || 'sites_group';
    this.breadCrumbElemnt['url'] = [
      this.breadCrumbElementBase.url,
      this.breadCrumbElemnt.id?.toString(),
    ].join('/');

    this.breadCrumbList = [this.breadCrumbElementBase, this.breadCrumbElemnt];
    this._objService.changeBreadCrumb(this.breadCrumbList, true);
  }

  ngOnDestroy() {
    this.geojsonService.removeFeatureGroup(this.geojsonService.sitesFeatureGroup);
  }
}
