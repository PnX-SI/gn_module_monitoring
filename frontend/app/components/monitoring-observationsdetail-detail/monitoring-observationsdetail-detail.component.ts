import { Component, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { GeoJSONService } from '../../services/geojson.service';
import { FormGroup, FormBuilder } from '@angular/forms';
import { ObservationDetailsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { SelectObject } from '../../interfaces/object';
import { FormService } from '../../services/form.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { resolveObjectProperties } from '../../utils/utils';
import { CacheService } from '../../services/cache.service';
import { IObservation } from '../../interfaces/observation';

@Component({
  selector: 'monitoring-observationsdetail-detail.component.css',
  templateUrl: './monitoring-observationsdetail-detail.component.html',
  styleUrls: ['./monitoring-observationsdetail-detail.component.css'],
})
export class MonitoringObservationsDetailDetailComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  private moduleCode: string;
  public moduleConfig;
  public currentUser;
  public objectType: string = 'observation_detail';
  private checkEditParam: boolean = false;
  public form: FormGroup;
  private dataId: number;
  public objectData: any;
  public objectDataResolved: any;
  public rows: Array<any> = [];

  bDeleteModalEmitter = new EventEmitter<boolean>();

  constructor(
    private _auth: AuthService,
    private router: Router,

    public _observationsDetailService: ObservationDetailsService,
    private _objService: ObjectService,
    private _Activatedroute: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _formBuilder: FormBuilder,
    public _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    private _cacheService: CacheService
  ) {
    super(_permissionService, _popup, _formService);
    this.getAllItemsCallback = undefined;
  }

  ngOnInit() {
    super.ngOnInit();
    // Initialisation des variables config
    this.moduleCode = this._configServiceG.moduleCode();
    this.moduleConfig = this._configServiceG.config();
    this.currentUser = this._auth.getCurrentUser();
    // Création d'un objet form
    this.form = this._formBuilder.group({});

    this._permissionService.setPermissionMonitorings(this.moduleCode);

    // Récupération des paramètres de la route
    this._Activatedroute.params.subscribe((params) => {
      this.dataId = params['id'];
      this.baseFilters = { id_observation: this.dataId };

      // breadcrumb
      const queryParams = this._Activatedroute.snapshot.queryParams;
      this.parentPath = queryParams['parents_path'];
      this.checkEditParam = JSON.parse(queryParams?.edit || 'false');
      if (this.checkEditParam === true) {
        this.bEdit = true;
        this._formService.changeCurrentEditMode(this.bEdit);
      }
      // Initialisation des données
      this.initData();
      this._objService.loadBreadCrumb(this.moduleCode, this.objectType, this.dataId, queryParams);

      this.setTemplateData(this.objectType);
    });
  }

  initData() {
    // Get data detail
    const fieldsConfig = this._configServiceG.config()[this.objectType]['fields'];
    this._observationsDetailService
      .getById(this.dataId, this.moduleCode)
      .subscribe((detailData) => {
        this.objectData = detailData;

        // Get site geometries
        this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
          id_base_site: this.objectData.id_base_site,
        });

        // Resolve data
        resolveObjectProperties(
          detailData,
          fieldsConfig,
          this._configServiceG,
          this._cacheService
        ).subscribe((data) => {
          this.objectDataResolved = data;
        });
      });
  }

  onbEditChange(event: boolean) {
    if (this.bEdit == true && event == false) {
      // Passage du mode édition au mode consultation : on suppose que des modifications de géométries
      //  ont pu être faites
      // Récupération et affichage de la géométrie du site
      this.initData();
    }
  }

  onDelete($event) {
    this._observationsDetailService
      .delete($event.rowSelected.id_observation_detail)
      .subscribe((del) => {
        this.bDeleteModalEmitter.emit(false);
        this.initData();
      });
  }
}
