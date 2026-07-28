import { Component, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { ISite } from '../../interfaces/geom';
import { IPaginated } from '../../interfaces/page';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { GeoJSONService } from '../../services/geojson.service';
import { FormGroup, FormBuilder } from '@angular/forms';
import { VisitsService, ObservationsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { SelectObject } from '../../interfaces/object';
import { FormService } from '../../services/form.service';
import { AuthService, User } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { resolveObjectProperties } from '../../utils/utils';
import { CacheService } from '../../services/cache.service';
import { IObservation } from '../../interfaces/observation';

@Component({
  selector: 'monitoring-visits-detail',
  templateUrl: './monitoring-visits-detail.component.html',
  styleUrls: ['./monitoring-visits-detail.component.css'],
})
export class MonitoringVisitsDetailComponent extends MonitoringGeomComponent implements OnInit {
  private moduleCode: string;
  public moduleConfig;
  public currentUser;
  public objectType: string = 'visit';
  private checkEditParam: boolean = false;
  public form: FormGroup;
  private dataId: number;
  public objectData: any;
  public objectDataResolved: any;
  public bEdit: boolean = false;
  public rows: Array<any> = [];

  bDeleteModalEmitter = new EventEmitter<boolean>();
  private currentEditModeSubscription: Subscription;

  constructor(
    private _auth: AuthService,
    private router: Router,
    public _visitsService: VisitsService,
    public _observationsService: ObservationsService,
    private _objService: ObjectService,
    private _Activatedroute: ActivatedRoute,
    private _geojsonService: GeoJSONService,
    private _formBuilder: FormBuilder,
    private _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    private _cacheService: CacheService
  ) {
    super(_permissionService, _popup);
    this.getAllItemsCallback = this.getChild;
  }

  ngOnInit() {
    this.currentEditModeSubscription = this._formService.currentEditMode.subscribe(
      (bEdit: boolean) => {
        // Permet d'identifier si l'objet est passé en mode édition
        // si c'est le cas, on refresh les données de l'objet
        this.onbEditChange(bEdit);
        this.bEdit = bEdit;
      }
    );
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
      this.baseFilters = { id_base_visit: this.dataId };

      // breadcrumb
      const queryParams = this._Activatedroute.snapshot.queryParams;
      this.parentPath = queryParams['parents_path'];
      this.checkEditParam = JSON.parse(queryParams?.edit || 'false');
      if (this.checkEditParam === true) {
        this.bEdit = true;
        this._formService.changeCurrentEditMode(this.bEdit);
      }
      // Initialisation des visites
      this.initData();
      this._objService.loadBreadCrumb(this.moduleCode, this.objectType, this.dataId, queryParams);

      this.setTemplateData(this.objectType);
    });
  }

  initData() {
    // Get visit detail data
    const fieldsConfig = this._configServiceG.config()[this.objectType]['fields'];
    this._visitsService.getById(this.dataId, this.moduleCode).subscribe((detailData) => {
      this.objectData = detailData;

      // Get site geometries
      this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
        id_base_site: this.objectData.id_base_site,
      });

      // Resolve visit data
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
    this._observationsService
      .getResolved(1, this.limit, { id_base_visit: this.dataId })
      .subscribe((data: IPaginated<ISite>) => {
        // Configuration du datatable
        this.rows = data.items;
        let dataTableData = {
          observations: {
            data: data,
            objType: 'observation',
            childType: 'observation_detail',
          },
        };
        this.setDataTableObjData(dataTableData, this.moduleCode, ['observation']);
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
      [`/monitorings/object/${this.moduleCode}/observation/${$event[$event.id]}`],
      { queryParams: queryParams }
    );
  }

  editChild($event) {
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
      edit: true,
      id_base_visit: this.dataId,
    };
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/observation/${$event[$event.id]}`],
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
      id_base_visit: this.dataId,
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
    });
  }

  ngOnDestroy() {
    this.currentEditModeSubscription.unsubscribe();
  }
}
