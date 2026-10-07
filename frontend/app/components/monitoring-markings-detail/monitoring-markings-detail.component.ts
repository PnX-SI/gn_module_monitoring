import { Component, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MonitoringGeomComponent } from '../../class/monitoring-geom-component';
import { Popup } from '../../utils/popup';
import { FormBuilder } from '@angular/forms';
import { MarkingsService } from '../../services/api-geom.service';
import { ObjectService } from '../../services/object.service';
import { FormService } from '../../services/form.service';
import { AuthService } from '@geonature/components/auth/auth.service';
import { PermissionService } from '../../services/permission.service';
import { DataUtilsService } from '../../services/data-utils.service';

@Component({
  selector: 'monitoring-markings-detail',
  templateUrl: './monitoring-markings-detail.component.html',
  styleUrls: ['./monitoring-markings-detail.component.css'],
})
export class MonitoringMarkingsDetailComponent extends MonitoringGeomComponent implements OnInit {
  public objectType: string = 'marking';

  bDeleteModalEmitter = new EventEmitter<boolean>();

  constructor(
    protected _Activatedroute: ActivatedRoute,
    protected _formBuilder: FormBuilder,
    protected _auth: AuthService,
    protected router: Router,
    public _markingsService: MarkingsService,
    private _objService: ObjectService,
    public _formService: FormService,
    public _permissionService: PermissionService,
    public _popup: Popup,
    protected _dataUtilsService: DataUtilsService
  ) {
    super(_permissionService, _popup, _formService, _Activatedroute, _formBuilder, _auth, router);
    this.getAllItemsCallback = undefined;
  }

  ngOnInit() {
    super.ngOnInit();
    this.baseFilters = { id_marking: this.dataId };
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
    this._markingsService.getById(this.dataId, this.moduleCode).subscribe((detailData) => {
      this.objectData = detailData;

      // Resolve data
      this._dataUtilsService.resolveObjectProperties(detailData, fieldsConfig).subscribe((data) => {
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
    this._markingsService.delete($event.rowSelected.id_marking).subscribe((del) => {
      this.bDeleteModalEmitter.emit(false);
      this.initData();
    });
  }
}
