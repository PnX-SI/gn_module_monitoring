import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
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
  private visitId: number;
  public currentUser;

  private checkEditParam: boolean = false;
  public form: FormGroup;
  public visitData: any;
  public visitDataResolved: any;
  public bEdit: boolean = false;
  public rows: Array<any> = [];
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
    this._formService.currentEditMode.subscribe((bEdit: boolean) => {
      // Permet d'identifier si l'objet est passé en mode édition
      // si c'est le cas, on refresh les données de l'objet
      this.onbEditChange(bEdit);
      this.bEdit = bEdit;
    });
    // Initialisation des variables config
    this.moduleCode = this._configServiceG.moduleCode();
    this.moduleConfig = this._configServiceG.config();
    this.currentUser = this._auth.getCurrentUser();
    // Création d'un objet form
    this.form = this._formBuilder.group({});

    this._visitsService.initConfig();
    this._observationsService.initConfig();
    this._permissionService.setPermissionMonitorings(this.moduleCode);

    // Récupération des paramètres de la route
    this._Activatedroute.params.subscribe((params) => {
      this.visitId = params['id'];
      this.baseFilters = { id_base_visit: this.visitId };

      // breadcrumb
      const queryParams = this._Activatedroute.snapshot.queryParams;
      this.parentPath = queryParams['parents_path'];
      this.checkEditParam = JSON.parse(queryParams?.edit || 'false');
      if (this.checkEditParam === true) {
        this.bEdit = true;
        this._formService.changeCurrentEditMode(this.bEdit);
      }
      // Initialisation des visites
      this.initVisit();
      this._objService.loadBreadCrumb(this.moduleCode, 'visit', this.visitId, queryParams);

      this.setTemplateData('visit');
    });
  }

  initVisit() {
    // Get visit detail data
    const fieldsConfig = this._configServiceG.config()['visit']['fields'];
    this._visitsService.getById(this.visitId, this.moduleCode).subscribe((visit) => {
      this.visitData = visit;

      // Get site geometries
      this._geojsonService.getSitesGroupsChildGeometries(this.onEachFeatureSite(), {
        id_base_site: this.visitData.id_base_site,
      });

      // Resolve visit data
      resolveObjectProperties(
        visit,
        fieldsConfig,
        this._configServiceG,
        this._cacheService
      ).subscribe((data) => {
        this.visitDataResolved = data;
      });
    });
    // Initialisation du datatable
    this._observationsService
      .getResolved(1, this.limit, { id_base_visit: this.visitId })
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
      this.initVisit();
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
      parents_path: [...this.parentPath, 'visit'],
    };
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/observation/${$event[$event.id]}`],
      { queryParams: queryParams }
    );
  }

  editChild($event) {
    const queryParams = {
      parents_path: [...this.parentPath, 'visit'],
      edit: true,
      id_base_visit: this.visitId,
    };
    this.router.navigate(
      [`/monitorings/object/${this.moduleCode}/observation/${$event[$event.id]}`],
      { queryParams: queryParams }
    );
  }

  onDelete($event) {
    this._observationsService.delete($event.rowSelected.id_observation).subscribe((del) => {
      this.initVisit();
    });
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: [...this.parentPath, 'visit'],
      id_base_visit: this.visitId,
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
    });
  }
}
