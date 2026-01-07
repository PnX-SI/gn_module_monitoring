import { Component, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Observable, of } from 'rxjs';
import { mergeMap, concatMap, tap } from 'rxjs/operators';

import { endPoints } from '../../enum/endpoints';
import { ISite, ISitesGroup, ISiteType } from '../../interfaces/geom';
import { IobjObs, ObjDataType } from '../../interfaces/objObs';
import { SitesGroupService, SitesService } from '../../services/api-geom.service';
import { FormService } from '../../services/form.service';
import { ObjectService } from '../../services/object.service';
import { JsonData } from '../../types/jsondata';
import { IPaginated } from '../../interfaces/page';
import { IBreadCrumb } from '../../interfaces/object';
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

  obj: MonitoringObject;
  bEdit: boolean = true;
  currentUser: User;
  moduleCode: string;
  sitesGroup: ISitesGroup;

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
    const idSitesGroup = this._route.snapshot.data.createSite.id_sites_group;
    this.moduleCode = this._route.snapshot.data.createSite.moduleCode;

    // breadcrumb
    const queryParams = this._route.snapshot.queryParams;
    this._objService.loadBreadCrumb(this.moduleCode, 'site', null, queryParams);

    this.bEdit = true;
    this.objForm = this._formBuilder.group({});
    const elements = document.getElementsByClassName('monitoring-map-container');
    if (elements.length >= 1) {
      elements[0].remove();
    }

    this.obj = new MonitoringObject(
      this.moduleCode,
      'site',
      null,
      this._monitoringObjServiceMonitoring
    );
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
      .subscribe(() => {
        this.obj.initTemplate();
        this._formService.changeFormMapObj({
          frmGp: this.objForm,
          obj: this.obj,
        });
        this._formService.changeCurrentEditMode(this.bEdit);
        this.obj.bIsInitialized = true;
      });
  }

  initConfig(): Observable<any> {
    return this._configService.init(this.moduleCode).pipe(
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

  ngOnDestroy() {
    this.geojsonService.removeSitesLayerGroup();
    this.geojsonService.removeFileLayerGroup();
    this._formService.changeCurrentEditMode(false);
    this._formService.changeFormMapObj({
      frmGp: null,
      obj: {},
    });
  }
}
