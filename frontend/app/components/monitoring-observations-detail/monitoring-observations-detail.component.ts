import { Component, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { ISite } from '../../interfaces/geom';
import { IPaginated } from '../../interfaces/page';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { GeoJSONService } from '../../services/geojson.service';
import { FormGroup, FormBuilder } from '@angular/forms';
import { ObservationsService, ObservationDetailsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { SelectObject } from '../../interfaces/object';
import { FormService } from '../../services/form.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { resolveObjectProperties } from '../../utils/utils';
import { CacheService } from '../../services/cache.service';
import { IObservation } from '../../interfaces/observation';
import { IObservationDetail } from '../../interfaces/observationdetail';

@Component({
  selector: 'monitoring-observations-detail',
  templateUrl: './monitoring-observations-detail.component.html',
  styleUrls: ['./monitoring-observations-detail.component.css'],
})
export class MonitoringObservationsDetailComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  public objectType: string = 'observation';

  public rows: Array<any> = [];

  bDeleteModalEmitter = new EventEmitter<boolean>();

  constructor(
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    private router: Router,
    public _observationsService: ObservationsService,
    public _observationsDetailService: ObservationDetailsService,
    private _objService: ObjectService,
    private _geojsonService: GeoJSONService,
    public _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    private _cacheService: CacheService
  ) {
    super(_permissionService, _popup, _formService, _Activatedroute, _formBuilder, _auth);
    this.getAllItemsCallback = this.getChild;
  }

  ngOnInit() {
    super.ngOnInit();
    this.baseFilters = { id_observation: this.dataId };
    // Initialisation des données
    this.initData();
    // breadcrumb
    this._objService.loadBreadCrumb(this.moduleCode, this.objectType, this.dataId, this.parentPath);
  }

  initData() {
    // Get data detail
    const fieldsConfig = this._configServiceG.config()[this.objectType]['fields'];
    this._observationsService.getById(this.dataId, this.moduleCode).subscribe((detailData) => {
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
    // Initialisation du datatable
    const childs_tree = this._configServiceG.getChildsByObjectType('observation');
    if (childs_tree.length == 0) {
      return;
    }
    this._observationsDetailService
      .getResolved(1, this.limit, { id_observation: this.dataId })
      .subscribe((data: IPaginated<IObservationDetail>) => {
        // Configuration du datatable
        this.rows = data.items;
        let dataTableData = {
          observations: {
            data: data,
            objType: 'observation_detail',
            childType: null,
          },
        };
        this.setDataTableObjData(dataTableData, this.moduleCode, ['observation_detail']);
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
  getChild(page: number, params) {
    const visitsParams = { ...params, ...this.baseFilters };

    // Mise à jour du datatable
    this._observationsService
      .getResolved(page, this.limit, visitsParams)
      .subscribe((data: IPaginated<IObservation>) => {
        this.rows = data.items;
        this.dataTableObjData.observation.rows = data.items;
        this.dataTableObjData.observation.page.count = data.count;
        this.dataTableObjData.observation.page.limit = data.limit;
        this.dataTableObjData.observation.page.page = data.page - 1;
      });
  }

  seeDetails($event) {
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
    };
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/observation_detail/${$event[$event.id]}`],
      { queryParams: queryParams }
    );
  }

  editChild($event) {
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
      edit: true,
      id_observation: this.dataId,
    };
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/observation_detail/${$event[$event.id]}`],
      { queryParams: queryParams }
    );
  }

  onDelete($event) {
    this._observationsService.delete($event.rowSelected.id_observation).subscribe((del) => {
      this.bDeleteModalEmitter.emit(false);
      this.initData();
    });
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
      id_observation: this.dataId,
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
    });
  }
}
