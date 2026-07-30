import { Component, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { FormGroup, FormBuilder } from '@angular/forms';
import { IndividualsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { FormService } from '../../services/form.service';
import { AuthService } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { resolveObjectProperties } from '../../utils/utils';
import { CacheService } from '../../services/cache.service';

@Component({
  selector: 'monitoring-individuals-detail',
  templateUrl: './monitoring-individuals-detail.component.html',
  styleUrls: ['./monitoring-individuals-detail.component.css'],
})
export class MonitoringIndividualsDetailComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  private moduleCode: string;
  public moduleConfig;
  public currentUser;
  public objectType: string = 'individual';
  private checkEditParam: boolean = false;
  public form: FormGroup;
  private dataId: number;
  public objectData: any;
  public objectDataResolved: any;
  public bEdit: boolean = false;

  bDeleteModalEmitter = new EventEmitter<boolean>();

  constructor(
    private _auth: AuthService,
    public _individualsService: IndividualsService,
    private _objService: ObjectService,
    private _Activatedroute: ActivatedRoute,
    private _formBuilder: FormBuilder,
    private _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    private _cacheService: CacheService
  ) {
    super(_permissionService, _popup);
    this.getAllItemsCallback = undefined;
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

    this._individualsService.initConfig();
    this._permissionService.setPermissionMonitorings(this.moduleCode);

    // Récupération des paramètres de la route
    this._Activatedroute.params.subscribe((params) => {
      this.dataId = params['id'];
      this.baseFilters = { id_individual: this.dataId };

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
    this._individualsService.getById(this.dataId, this.moduleCode).subscribe((detailData) => {
      this.objectData = detailData;

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
      // Passage du mode édition au mode consultation
      this.initData();
    }
  }

  onDelete($event) {
    this._individualsService.delete($event.rowSelected.id_individual).subscribe((del) => {
      this.bDeleteModalEmitter.emit(false);
      this.initData();
    });
  }
}
