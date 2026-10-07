import { Component, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { FormBuilder } from '@angular/forms';
import { IndividualsService, MarkingsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { FormService } from '../../services/form.service';
import { AuthService } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { IPaginated } from '../../interfaces/page';
import { IMarking } from '../../interfaces/marking';
import { DataUtilsService } from '../../services/data-utils.service';

@Component({
  selector: 'monitoring-individuals-detail',
  templateUrl: './monitoring-individuals-detail.component.html',
  styleUrls: ['./monitoring-individuals-detail.component.css'],
})
export class MonitoringIndividualsDetailComponent
  extends MonitoringGeomComponent
  implements OnInit
{
  public objectType: string = 'individual';
  public rows: Array<any> = [];
  public allowedObjectTypes: string[] = ['marking'];

  bDeleteModalEmitter = new EventEmitter<boolean>();

  constructor(
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    protected router: Router,
    public _individualsService: IndividualsService,
    public _markingsService: MarkingsService,
    private _objService: ObjectService,
    public _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    protected _dataUtilsService: DataUtilsService
  ) {
    super(_permissionService, _popup, _formService, _Activatedroute, _formBuilder, _auth, router);
    this.getAllItemsCallback = this.getChild;
  }

  ngOnInit() {
    super.ngOnInit();
    this.baseFilters = { id_individual: this.dataId };
    // Initialisation des données
    this.initData();
    // breadcrumb
    this._objService.loadBreadCrumb(
      this.moduleCode,
      this.objectType,
      this.dataId,
      this.queryParams
    );
  }

  initData() {
    // Get data detail
    const fieldsConfig = this._configServiceG.config()[this.objectType]['fields'];
    this._individualsService.getById(this.dataId, this.moduleCode).subscribe((detailData) => {
      this.objectData = detailData;

      // Resolve data
      this._dataUtilsService.resolveObjectProperties(detailData, fieldsConfig).subscribe((data) => {
        this.objectDataResolved = data;
      });
    });
    // Initialisation du datatable des marquages
    const defaultFilters = {
      ...(this._configServiceG.config()['marking']?.['filters'] || {}),
      ...this.baseFilters,
    };
    this._markingsService
      .getResolved(1, this.limit, defaultFilters)
      .subscribe((data: IPaginated<IMarking>) => {
        this.rows = data.items;
        let dataTableData = {
          marking: {
            data: data,
            objType: 'marking',
            childType: null,
          },
        };
        this.setDataTableObjData(dataTableData, this.moduleCode, ['marking']);
      });
  }

  onbEditChange(event: boolean) {
    if (this.bEdit == true && event == false) {
      // Passage du mode édition au mode consultation
      this.initData();
    }
  }

  getChild(page: number, params) {
    const markingsParams = { ...params, ...this.baseFilters };

    // Mise à jour du datatable
    this._markingsService
      .getResolved(page, this.limit, markingsParams)
      .subscribe((data: IPaginated<IMarking>) => {
        this.rows = data.items;
        this.dataTableObjData.marking.rows = data.items;
        this.dataTableObjData.marking.page.count = data.count;
        this.dataTableObjData.marking.page.limit = data.limit;
        this.dataTableObjData.marking.page.page = data.page - 1;
      });
  }

  seeDetails($event) {
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/marking/${$event[$event.id]}`], {
      queryParams: queryParams,
    });
  }

  editChild($event) {
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
      edit: true,
      id_individual: this.dataId,
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/marking/${$event[$event.id]}`], {
      queryParams: queryParams,
    });
  }

  onDelete($event) {
    this._markingsService.delete($event.rowSelected.id_marking).subscribe((del) => {
      this.bDeleteModalEmitter.emit(false);
      this.initData();
    });
  }

  navigateToAddObj($event) {
    const type = $event;
    const queryParams = {
      parents_path: [...this.parentPath, this.objectType],
      id_individual: this.dataId,
    };
    this.router.navigate([`/monitorings/object/${this.moduleCode}/`, type, 'create'], {
      queryParams: queryParams,
    });
  }
}
